#!/usr/bin/env python3
"""
merge_adapter.py
Merge LoRA adapter into base model for Ollama ingestion.

Usage:
    python merge_adapter.py --base_model meta-llama/Meta-Llama-3.2-3B-Instruct --adapter adapters/intent_parser --output models/intent_parser_merged
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
    
    # Load base model (without quantization for merging)
    print(f"Loading base model: {args.base_model}")
    base_model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.bfloat16,
        device_map="auto",
        trust_remote_code=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    
    # Load adapter
    print(f"Loading adapter: {args.adapter}")
    model = PeftModel.from_pretrained(base_model, str(args.adapter))
    
    # Merge adapter into base
    print("Merging adapter into base model...")
    model = model.merge_and_unload()
    
    # Save merged model
    print(f"Saving merged model to: {args.output}")
    args.output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    
    print(f"Merged model saved to {args.output}")


if __name__ == "__main__":
    main()

