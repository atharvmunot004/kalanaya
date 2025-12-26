#!/usr/bin/env python3
"""
merge_adapter_simple.py
Simple merge script that loads everything on CPU to avoid device_map issues.
"""

import argparse
from pathlib import Path
import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer


def main():
    parser = argparse.ArgumentParser(description="Merge LoRA adapter into base model")
    parser.add_argument("--base_model", type=str, required=True, help="Base model name or path")
    parser.add_argument("--adapter", type=Path, required=True, help="Path to LoRA adapter")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for merged model")
    
    args = parser.parse_args()
    
    print(f"Loading base model on CPU: {args.base_model}")
    # Load on CPU first to avoid device_map issues
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float32,  # Use float32 for merging on CPU
        device_map=None,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    
    print(f"Loading adapter: {args.adapter}")
    model = PeftModel.from_pretrained(base_model, str(args.adapter))
    
    print("Merging adapter into base model...")
    model = model.merge_and_unload()
    
    print(f"Saving merged model to: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    
    # Save with safe serialization
    model.save_pretrained(str(args.output), safe_serialization=True)
    tokenizer.save_pretrained(str(args.output))
    
    print(f"[OK] Merged model saved to {args.output}")


if __name__ == "__main__":
    main()


