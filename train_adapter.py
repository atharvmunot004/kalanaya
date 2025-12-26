#!/usr/bin/env python3
"""
train_adapter.py
QLoRA training script for agent-specific adapters.

Usage:
    python train_adapter.py --dataset datasets/intent_parser.jsonl --output adapters/intent_parser
    python train_adapter.py --dataset datasets/entity_parser.jsonl --output adapters/entity_parser
    python train_adapter.py --dataset datasets/time_parser.jsonl --output adapters/time_parser
    python train_adapter.py --dataset datasets/validator.jsonl --output adapters/validator
"""

import argparse
import json
from pathlib import Path
from typing import Dict, Any

import torch
from datasets import Dataset
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    BitsAndBytesConfig,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
)

# Base model configuration
# Note: Meta Llama models are gated and require authentication
# Authenticate first: huggingface-cli login
# Or pass --hf_token argument
# For local testing, you can use a local path or alternative models
# Alternative models: meta-llama/Llama-3-8B-Instruct, meta-llama/Llama-2-7b-chat-hf
# Or use a local path if you have the model downloaded
BASE_MODEL = "meta-llama/Llama-3.2-3B-Instruct"


def load_dataset(jsonl_path: Path) -> Dataset:
    """Load JSONL dataset into HuggingFace Dataset format."""
    data = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data.append(json.loads(line))
    
    return Dataset.from_list(data)


def format_prompt(example: Dict[str, Any]) -> str:
    """Format instruction-input-output into prompt for instruction tuning."""
    instruction = example["instruction"]
    user_input = example["input"]
    output = example["output"]
    
    # Format as instruction-following prompt
    prompt = f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{instruction}<|eot_id|><|start_header_id|>user<|end_header_id|>\n\n{user_input}<|eot_id|><|start_header_id|>assistant<|end_header_id|>\n\n{output}<|eot_id|>"
    
    return prompt


def tokenize_function(examples: Dict[str, Any], tokenizer: AutoTokenizer) -> Dict[str, Any]:
    """Tokenize examples for training."""
    prompts = [format_prompt({"instruction": i, "input": inp, "output": o}) 
               for i, inp, o in zip(examples["instruction"], examples["input"], examples["output"])]
    
    # Tokenize with padding
    tokenized = tokenizer(
        prompts,
        truncation=True,
        padding="max_length",
        max_length=512,
        return_tensors=None,
    )
    
    # Labels are the same as input_ids (model learns to generate next token given context)
    # Note: For proper instruction tuning, you might want to mask input tokens (set to -100)
    # but for small datasets, this simpler approach works
    tokenized["labels"] = tokenized["input_ids"].copy()
    
    return tokenized


def main():
    parser = argparse.ArgumentParser(description="Train QLoRA adapter for agent")
    parser.add_argument("--dataset", type=Path, required=True, help="Path to JSONL dataset")
    parser.add_argument("--output", type=Path, required=True, help="Output directory for adapter")
    parser.add_argument("--base_model", type=str, default=BASE_MODEL, help="Base model name or local path")
    parser.add_argument("--hf_token", type=str, default=None, help="HuggingFace token for gated models")
    parser.add_argument("--epochs", type=int, default=3, help="Number of training epochs")
    parser.add_argument("--learning_rate", type=float, default=2e-4, help="Learning rate")
    parser.add_argument("--batch_size", type=int, default=4, help="Training batch size")
    parser.add_argument("--gradient_accumulation_steps", type=int, default=4, help="Gradient accumulation steps")
    
    args = parser.parse_args()
    
    # Load tokenizer
    tokenizer_kwargs = {}
    if args.hf_token:
        tokenizer_kwargs["token"] = args.hf_token
    
    tokenizer = AutoTokenizer.from_pretrained(args.base_model, **tokenizer_kwargs)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    # Check CUDA availability
    use_cuda = torch.cuda.is_available()
    if use_cuda:
        print(f"[OK] Using CUDA device: {torch.cuda.get_device_name(0)}")
        print(f"[OK] CUDA memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        print("[ERROR] CUDA not available in PyTorch")
        print("  You have a GPU (detected via nvidia-smi), but PyTorch was installed without CUDA support")
        print("  Install CUDA-enabled PyTorch:")
        print("  pip uninstall torch torchvision torchaudio")
        print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121")
        sys.exit(1)
    
    # Configure 4-bit quantization (requires CUDA)
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    
    # Load base model with quantization
    model_kwargs = {
        "quantization_config": bnb_config,
        "device_map": "auto",
        "dtype": torch.bfloat16,
        "trust_remote_code": True,
    }
    if args.hf_token:
        model_kwargs["token"] = args.hf_token
    
    model = AutoModelForCausalLM.from_pretrained(args.base_model, **model_kwargs)
    
    # Prepare model for k-bit training
    model = prepare_model_for_kbit_training(model)
    
    # Configure LoRA
    # Detect model architecture to set correct target modules
    model_type = model.config.model_type if hasattr(model.config, 'model_type') else None
    if model_type == "phi3":
        # Phi-3 uses qkv_proj (combined) and o_proj
        target_modules = ["qkv_proj", "o_proj"]
    elif "llama" in model_type.lower() if model_type else False:
        # Llama models use separate q_proj, v_proj, k_proj, o_proj
        target_modules = ["q_proj", "v_proj"]
    else:
        # Default: try common module names
        target_modules = ["q_proj", "v_proj", "qkv_proj", "o_proj"]
    
    lora_config = LoraConfig(
        r=16,
        lora_alpha=32,
        target_modules=target_modules,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
    )
    
    # Apply LoRA
    model = get_peft_model(model, lora_config)
    
    # Load and prepare dataset
    dataset = load_dataset(args.dataset)
    tokenized_dataset = dataset.map(
        lambda examples: tokenize_function(examples, tokenizer),
        batched=True,
        remove_columns=dataset.column_names,
    )
    
    # Data collator
    data_collator = DataCollatorForLanguageModeling(
        tokenizer=tokenizer,
        mlm=False,
    )
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir=str(args.output / "checkpoints"),
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.gradient_accumulation_steps,
        learning_rate=args.learning_rate,
        fp16=False,
        bf16=use_cuda,  # bf16 requires CUDA
        logging_steps=10,
        save_steps=100,
        save_total_limit=2,
        warmup_steps=50,
        optim="paged_adamw_8bit" if use_cuda else "adamw_torch",
        lr_scheduler_type="cosine",
        report_to="none",
    )
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_dataset,
        data_collator=data_collator,
    )
    
    # Train
    trainer.train()
    
    # Save adapter
    args.output.mkdir(parents=True, exist_ok=True)
    model.save_pretrained(str(args.output))
    tokenizer.save_pretrained(str(args.output))
    
    print(f"Adapter saved to {args.output}")


if __name__ == "__main__":
    main()

