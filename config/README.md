# Config Directory

Configuration files for Kalanaya.

## Files

- `intent_prompt.txt` - Prompt template for the intent parsing engine
- `intent_schema.json` - JSON schema for intent output format
- `settings.py` - Python configuration settings

## Intent Prompt

The `intent_prompt.txt` file contains the prompt template used by the Ollama LLM to parse user intents into structured JSON. It includes:

- Instructions for the LLM
- Current date/time placeholders ({{CURRENT_DATE}}, {{CURRENT_TIME}}, etc.)
- Rules for handling dates, times, and actions
- Output schema definition

## Intent Schema

The `intent_schema.json` file defines the expected structure of parsed intents, including:

- Action types (create_event, update_event, delete_event, list_events, none)
- Required and optional fields
- Data types and constraints

