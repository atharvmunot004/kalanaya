#!/usr/bin/env python3
"""
merge_all_adapters.py
Merge all LoRA adapters into base model for Ollama ingestion.
"""

import subprocess
import sys
from pathlib import Path

BASE_MODEL = "microsoft/Phi-3-mini-4k-instruct"

AGENTS = [
    ("intent_parser", "adapters/intent_parser", "models/intent_parser_merged"),
    ("entity_parser", "adapters/entity_parser", "models/entity_parser_merged"),
    ("time_parser", "adapters/time_parser", "models/time_parser_merged"),
    ("validator", "adapters/validator", "models/validator_merged"),
]

def main():
    for agent_name, adapter_path, output_path in AGENTS:
        print(f"\n{'='*60}")
        print(f"Merging {agent_name} adapter...")
        print(f"{'='*60}\n")
        
        # Check if adapter exists
        if not Path(adapter_path).exists():
            print(f"ERROR: Adapter not found at {adapter_path}")
            sys.exit(1)
        
        cmd = [
            sys.executable,
            "merge_adapter_simple.py",
            "--base_model", BASE_MODEL,
            "--adapter", adapter_path,
            "--output", output_path,
        ]
        
        result = subprocess.run(cmd, check=False)
        
        if result.returncode != 0:
            print(f"\nERROR: Merging {agent_name} failed with exit code {result.returncode}")
            sys.exit(1)
        
        print(f"\n[OK] {agent_name} merged successfully")
    
    print(f"\n{'='*60}")
    print("All adapters merged successfully!")
    print(f"{'='*60}")

if __name__ == "__main__":
    main()

