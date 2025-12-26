#!/usr/bin/env python3
"""
merge_adapter_direct.py
Merge LoRA adapter weights directly into base model.
"""

import argparse
from pathlib import Path
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftConfig
import json


def merge_lora_weights(base_model, adapter_path):
    """Merge LoRA weights directly into base model state dict."""
    adapter_config = PeftConfig.from_pretrained(adapter_path)
    adapter_state_dict = torch.load(Path(adapter_path) / "adapter_model.bin", map_location="cpu")
    
    base_state_dict = base_model.state_dict()
    
    # Merge LoRA weights: base_weight + (lora_B @ lora_A) * (alpha / r)
    alpha = adapter_config.lora_alpha
    r = adapter_config.r
    
    for key in adapter_state_dict:
        if "lora_A" in key:
            # Get corresponding lora_B key
            lora_b_key = key.replace("lora_A", "lora_B")
            if lora_b_key in adapter_state_dict:
                # Get base weight key (remove lora_A.default. prefix)
                base_key = key.replace(".lora_A.default.weight", "").replace("base_model.model.model.", "")
                
                # Find the actual base key in state dict
                actual_base_key = None
                for k in base_state_dict.keys():
                    if base_key in k and "lora" not in k:
                        actual_base_key = k
                        break
                
                if actual_base_key and actual_base_key in base_state_dict:
                    lora_a = adapter_state_dict[key]
                    lora_b = adapter_state_dict[lora_b_key]
                    
                    # LoRA delta = lora_B @ lora_A
                    if len(lora_a.shape) == 2:
                        delta = torch.mm(lora_b, lora_a) * (alpha / r)
                    else:
                        delta = torch.einsum('i j, j k -> i k', lora_b, lora_a) * (alpha / r)
                    
                    # Add delta to base weight
                    base_state_dict[actual_base_key] = base_state_dict[actual_base_key].to(delta.dtype) + delta.to(base_state_dict[actual_base_key].device)
    
    base_model.load_state_dict(base_state_dict)
    return base_model


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("--base_model", type=str, required=True, help="Base model name or path")
    parser.add_argument("--adapter", type=Path, required=True, help="Path to LoRA adapter")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for merged model")
    
    args = parser.parse_args()
    
    print(f"Loading base model: {args.base_model}")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    
    print(f"Loading and merging adapter: {args.adapter}")
    merged_model = merge_lora_weights(base_model, args.adapter)
    
    print(f"Saving merged model to: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    merged_model.save_pretrained(str(args.output), safe_serialization=True)
    tokenizer.save_pretrained(str(args.output))
    
    print(f"[OK] Merged model saved to {args.output}")


if __name__ == "__main__":
    main()


