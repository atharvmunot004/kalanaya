#!/bin/bash
# create_ollama_models.sh
# Create Ollama models from Modelfiles

# Navigate to ollama directory
cd "$(dirname "$0")/../ollama" || exit

# Create each agent model
ollama create kalanaya-intent-parser -f Modelfile.intent_parser
ollama create kalanaya-entity-parser -f Modelfile.entity_parser
ollama create kalanaya-time-parser -f Modelfile.time_parser
ollama create kalanaya-validator -f Modelfile.validator

echo "All agent models created successfully"

