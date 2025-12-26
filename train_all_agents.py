#!/usr/bin/env python3
"""
train_all_agents.py
Train LoRA adapters for all agents sequentially.
"""

import subprocess
import sys
from pathlib import Path

AGENTS = [
    ("intent_parser", "datasets/intent_parser.jsonl", "adapters/intent_parser"),
    ("entity_parser", "datasets/entity_parser.jsonl", "adapters/entity_parser"),
    ("time_parser", "datasets/time_parser.jsonl", "adapters/time_parser"),
    ("validator", "datasets/validator.jsonl", "adapters/validator"),
]

def main():
    for agent_name, dataset_path, output_path in AGENTS:
        print(f"\n{'='*60}")
        print(f"Training {agent_name}...")
        print(f"{'='*60}\n")
        
        cmd = [
            sys.executable,
            "train_adapter.py",
            "--dataset", dataset_path,
            "--output", output_path,
        ]
        
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print(f"\nERROR: Training {agent_name} failed with exit code {result.returncode}")
            sys.exit(1)
        
        print(f"\n✓ {agent_name} training completed")
    
    print(f"\n{'='*60}")
    print("All agents trained successfully!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

