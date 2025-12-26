# create_ollama_models.ps1
# Create Ollama models from Modelfiles

$OllamaDir = Join-Path $PSScriptRoot ".." "ollama"
Set-Location $OllamaDir

# Create each agent model
ollama create kalanaya-intent-parser -f Modelfile.intent_parser
ollama create kalanaya-entity-parser -f Modelfile.entity_parser
ollama create kalanaya-time-parser -f Modelfile.time_parser
ollama create kalanaya-validator -f Modelfile.validator

Write-Host "All agent models created successfully"

