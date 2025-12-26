# Model Usage Documentation

## Overview
This document describes how the fine-tuned LoRA adapter models are used in the Kalanaya pipeline.

## Fine-Tuned Models

The project uses four fine-tuned LoRA adapter models, each specialized for a specific task:

1. **kalanaya-intent-parser** - Intent classification (Level 1)
2. **kalanaya-entity-parser** - Semantic field extraction (Level 2)
3. **kalanaya-time-parser** - Time/date extraction (Level 2)
4. **kalanaya-validator** - Field validation (Level 3) - Currently not used (validation is code-based)

## Model Usage by Pipeline Stage

### Level 1: Intent Classification
- **File**: `src/pipeline/level1_intent.py`
- **Model**: `kalanaya-intent-parser`
- **Purpose**: Classifies user input into one of: `create_event`, `update_event`, `delete_event`, `list_events`, or `unknown`
- **Function**: `classify_intent()`

### Level 2: Field Extraction

#### Create Event
- **File**: `src/pipeline/level2_extraction.py`
- **Function**: `extract_fields_create_event()`
- **Models Used**:
  - `kalanaya-entity-parser` - Extracts semantic fields (title, description, location)
  - `kalanaya-time-parser` - Extracts time fields (start_time, end_time, all_day)

#### Update Event
- **File**: `src/pipeline/level2_extraction.py`
- **Function**: `extract_fields_update_event()`
- **Model**: `kalanaya-entity-parser` - Extracts event identifier and updated fields

#### Delete Event
- **File**: `src/pipeline/level2_extraction.py`
- **Function**: `extract_fields_delete_event()`
- **Model**: `kalanaya-entity-parser` - Extracts event identifier

#### List Events
- **File**: `src/pipeline/level2_extraction.py`
- **Function**: `extract_fields_list_events()`
- **Model**: `kalanaya-time-parser` - Extracts time range (start_time, end_time)

### Level 3: Validation
- **File**: `src/pipeline/level3_validation.py`
- **Model**: None (code-based validation)
- **Note**: The `kalanaya-validator` model exists but is not currently used. Validation is performed deterministically in code.

## Model Configuration

Models are configured in:
- `src/pipeline/level1_intent.py` - Intent parser model
- `src/pipeline/level2_extraction.py` - Entity and time parser models
- `config/settings.py` - Central configuration (for reference)

## Creating Models

To create the Ollama models from the Modelfiles, run:

```powershell
# Windows
.\scripts\create_ollama_models.ps1

# Linux/Mac
./scripts/create_ollama_models.sh
```

This will create the following models in Ollama:
- `kalanaya-intent-parser`
- `kalanaya-entity-parser`
- `kalanaya-time-parser`
- `kalanaya-validator`

## Fallback Behavior

If a fine-tuned model is not available or fails, the code falls back to:
- `llama3.2:latest` (base model)

However, this should be avoided as the fine-tuned models provide better accuracy for their specific tasks.

## Model Requirements

Before running the application, ensure:
1. Ollama is running: `ollama serve`
2. All fine-tuned models are created: Run the create_ollama_models script
3. Models are available: `ollama list` should show all kalanaya-* models

## Testing

The test suite mocks Ollama API calls, so tests don't require the models to be available. However, for actual usage, the models must be created and available in Ollama.

