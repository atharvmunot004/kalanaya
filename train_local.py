#!/usr/bin/env python3
"""
train_local.py
Train LoRA adapters using a publicly available model (no authentication required).
Uses Microsoft Phi-3-mini as it's publicly available and works well for fine-tuning.
"""

import subprocess
import sys

# Use a publicly available model that doesn't require authentication
PUBLIC_MODEL = "microsoft/Phi-3-mini-4k-instruct"

AGENTS = [
    ("intent_parser", "datasets/intent_parser.jsonl", "adapters/intent_parser"),
    ("entity_parser", "datasets/entity_parser.jsonl", "adapters/entity_parser"),
    ("time_parser", "datasets/time_parser.jsonl", "adapters/time_parser"),
    ("validator", "datasets/validator.jsonl", "adapters/validator"),
]

def main():
    for agent_name, dataset_path, output_path in AGENTS:
        print(f"\n{'='*60}")
        print(f"Training {agent_name} with {PUBLIC_MODEL}...")
        print(f"{'='*60}\n")
        
        cmd = [
            sys.executable,
            "train_adapter.py",
            "--dataset", dataset_path,
            "--output", output_path,
            "--base_model", PUBLIC_MODEL,
        ]
        
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print(f"\nERROR: Training {agent_name} failed with exit code {result.returncode}")
            sys.exit(1)
        
        print(f"\n[OK] {agent_name} training completed")
    
    print(f"\n{'='*60}")
    print("All agents trained successfully!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

