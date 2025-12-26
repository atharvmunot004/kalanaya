"""Configuration settings for Kalanaya."""

from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Directories
CONFIG_DIR = PROJECT_ROOT / "config"
CREDENTIALS_DIR = PROJECT_ROOT / "credentials"
TEST_RESULTS_DIR = PROJECT_ROOT / "test_results"

# Credentials
CREDENTIALS_FILE = CREDENTIALS_DIR / "google_client_secret.json"
TOKEN_FILE = CREDENTIALS_DIR / "token.pickle"

# Config files
INTENT_PROMPT_FILE = CONFIG_DIR / "intent_prompt.txt"
INTENT_SCHEMA_FILE = CONFIG_DIR / "intent_schema.json"

# Ollama settings
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "llama3.2:latest"  # Base model (fallback)
# Fine-tuned LoRA adapter models
OLLAMA_MODEL_INTENT_PARSER = "kalanaya-intent-parser"
OLLAMA_MODEL_ENTITY_PARSER = "kalanaya-entity-parser"
OLLAMA_MODEL_TIME_PARSER = "kalanaya-time-parser"
OLLAMA_MODEL_VALIDATOR = "kalanaya-validator"

# Calendar settings
CALENDAR_SCOPES = ['https://www.googleapis.com/auth/calendar']
DEFAULT_TIMEZONE = "Asia/Kolkata"

# Speech settings
SAMPLE_RATE = 16000  # Whisper prefers 16kHz
DEFAULT_RECORDING_DURATION = 5  # seconds

