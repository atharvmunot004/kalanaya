# LoRA Training Setup

## Prerequisites

1. **HuggingFace Authentication** (required for Meta Llama models):
   ```bash
   huggingface-cli login
   ```
   You'll need a HuggingFace token with access to Meta Llama models.

2. **Dependencies**:
   ```bash
   pip install torch transformers peft bitsandbytes accelerate datasets
   ```

3. **CUDA GPU** (recommended, but CPU will work slowly):
   - Training requires significant compute resources
   - CUDA-enabled GPU strongly recommended

## Training

Train all agents:
```bash
python train_all_agents.py
```

Train individual agent:
```bash
python train_adapter.py --dataset datasets/intent_parser.jsonl --output adapters/intent_parser
```

## Model Access

Meta Llama models are gated and require:
- HuggingFace account with approved access
- Authentication via `huggingface-cli login`

If you don't have access, you can:
1. Request access at: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct
2. Use an alternative base model by specifying `--base_model` argument

## After Training

1. Merge adapters:
   ```bash
   python merge_adapter.py --base_model meta-llama/Llama-3.2-3B-Instruct --adapter adapters/intent_parser --output models/intent_parser_merged
   ```

2. Create Ollama models:
   ```bash
   cd ollama
   ollama create kalanaya-intent-parser -f Modelfile.intent_parser
   # ... repeat for other agents
   ```

