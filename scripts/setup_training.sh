#!/bin/bash
# setup_training.sh
# Setup script for LoRA training

echo "Setting up LoRA training environment..."
echo ""

# Check if huggingface-cli is available
if ! command -v huggingface-cli &> /dev/null; then
    echo "Installing huggingface-hub..."
    pip install huggingface-hub
fi

# Check authentication
echo "Checking HuggingFace authentication..."
if huggingface-cli whoami &> /dev/null; then
    echo "✓ Authenticated as: $(huggingface-cli whoami)"
else
    echo "✗ Not authenticated"
    echo ""
    echo "Please authenticate with HuggingFace:"
    echo "  huggingface-cli login"
    echo ""
    echo "You'll need a HuggingFace token with access to Meta Llama models."
    echo "Request access at: https://huggingface.co/meta-llama/Llama-3.2-3B-Instruct"
    exit 1
fi

echo ""
echo "Setup complete. You can now run: python train_all_agents.py"

