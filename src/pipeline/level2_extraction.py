"""Level 2: Intent-Specific Field Extraction - Extract fields based on locked intent."""

import requests
import json
import re
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

# Try to use zoneinfo (Python 3.9+), fallback to UTC offset for Windows compatibility
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Kolkata")
except (ImportError, ModuleNotFoundError, LookupError):
    # Fallback: Asia/Kolkata is UTC+5:30
    TZ = timezone(timedelta(hours=5, minutes=30))

OLLAMA_URL = "http://localhost:11434/api/generate"
# Default model (fallback), but specific models are used for different extraction tasks
MODEL = "llama3.2:latest"  # Fallback model
MODEL_ENTITY_PARSER = "kalanaya-entity-parser"  # Fine-tuned LoRA adapter for semantic extraction
MODEL_TIME_PARSER = "kalanaya-time-parser"  # Fine-tuned LoRA adapter for time extraction

# Load prompt templates
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_PROMPTS_DIR = _PROJECT_ROOT / "prompts"

with open(_PROMPTS_DIR / "level2_create_semantic.llama.txt", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE_CREATE_SEMANTIC = f.read()
with open(_PROMPTS_DIR / "level2_create_time.llama.txt", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE_CREATE_TIME = f.read()
with open(_PROMPTS_DIR / "level2_update_event.llama.txt", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE_UPDATE = f.read()
with open(_PROMPTS_DIR / "level2_delete_event.llama.txt", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE_DELETE = f.read()
with open(_PROMPTS_DIR / "level2_list_events.llama.txt", "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE_LIST = f.read()


def _get_temporal_anchors() -> Dict[str, str]:
    """Get current date/time information for prompts."""
    now = datetime.now(TZ)
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after_tomorrow = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    return {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "current_datetime_iso": now.isoformat(),
        "current_day_name": now.strftime("%A"),
        "current_date_readable": now.strftime("%B %d, %Y"),
        "current_year": str(now.year),
        "tomorrow": tomorrow,
        "day_after_tomorrow": day_after_tomorrow,
    }


def _call_ollama(prompt: str, model: str = None) -> str:
    """
    Call Ollama API with the given prompt.
    
    Args:
        prompt: The prompt to send to Ollama
        model: Model name to use (defaults to MODEL constant)
    """
    model_to_use = model if model is not None else MODEL
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": model_to_use,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        },
        timeout=60,
    )
    
    response.raise_for_status()
    response_data = response.json()
    
    if "error" in response_data:
        raise Exception(f"Ollama API error: {response_data['error']}")
    
    if "response" in response_data:
        return response_data["response"].strip()
    elif "content" in response_data:
        return response_data["content"].strip()
    elif isinstance(response_data, str):
        return response_data.strip()
    else:
        raise KeyError(f"'response' key not found in Ollama API response. Available keys: {list(response_data.keys())}")


def _parse_json_from_llm_response(response_text: str, logger=None) -> Dict[str, Any]:
    """
    Robustly parse JSON from LLM response.
    
    Handles:
    - Empty responses
    - Markdown code blocks
    - Text before/after JSON
    - Single quotes (converts to double)
    - Trailing commas
    - Common JSON formatting issues
    
    Args:
        response_text: Raw response from LLM
        logger: Optional logger for debugging
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        json.JSONDecodeError: If JSON cannot be parsed after all attempts
    """
    if not response_text or not response_text.strip():
        raise ValueError("Empty response from LLM")
    
    response_text = response_text.strip()
    
    # Remove markdown code fences
    if response_text.startswith("```"):
        lines = response_text.split("\n")
        json_lines = []
        in_json = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("```"):
                in_json = not in_json
                continue
            if in_json:
                json_lines.append(line)
        if json_lines:
            response_text = "\n".join(json_lines).strip()
    
    # Extract JSON object if embedded in text
    if "{" in response_text and "}" in response_text:
        start_idx = response_text.find("{")
        end_idx = response_text.rfind("}") + 1
        if start_idx >= 0 and end_idx > start_idx:
            response_text = response_text[start_idx:end_idx]
    
    # Try direct parse first
    try:
        return json.loads(response_text)
    except json.JSONDecodeError:
        pass
    
    # Try fixing common issues
    # Replace single quotes with double quotes (but be careful with apostrophes in strings)
    # This is a simple approach - for production, consider using ast.literal_eval or a more sophisticated parser
    fixed = response_text
    
    # Remove trailing commas before closing braces/brackets
    fixed = re.sub(r',(\s*[}\]])', r'\1', fixed)
    
    # Try parsing again
    try:
        return json.loads(fixed)
    except json.JSONDecodeError:
        pass
    
    # Log the problematic response for debugging
    if logger:
        logger.error(f"Failed to parse JSON. Response (first 500 chars): {response_text[:500]}")
    
    # Last attempt: try to extract just the JSON structure
    # Find the first { and last } and try again
    if "{" in fixed and "}" in fixed:
        start = fixed.find("{")
        end = fixed.rfind("}") + 1
        if start >= 0 and end > start:
            try:
                return json.loads(fixed[start:end])
            except json.JSONDecodeError:
                pass
    
    # If all else fails, raise a ValueError with details
    raise ValueError(f"Could not parse JSON from LLM response. First 200 chars: {response_text[:200]}")


def extract_fields_create_event(user_input: str) -> Dict[str, Any]:
    """
    Extract fields for create_event intent using split semantic and time parsers.
    
    Args:
        user_input: User's text input
        
    Returns:
        Dictionary with extracted fields according to create_event schema
    """
    anchors = _get_temporal_anchors()
    
    # Step 1: Extract semantic fields (title, description, location)
    prompt_semantic = PROMPT_TEMPLATE_CREATE_SEMANTIC.replace("{{USER_INPUT}}", user_input)
    
    import logging
    logger = logging.getLogger(__name__)
    
    response_semantic = None
    try:
        # Use fine-tuned entity parser model for semantic extraction
        response_semantic = _call_ollama(prompt_semantic, model=MODEL_ENTITY_PARSER)
        semantic_result = _parse_json_from_llm_response(response_semantic, logger)
        
        # Ensure action field is set
        if "action" not in semantic_result:
            semantic_result["action"] = "create_event"
    except Exception as e:
        logger.error(f"Error extracting semantic fields: {str(e)}")
        # Log the raw response for debugging if we have it
        if response_semantic:
            logger.debug(f"Raw semantic response: {response_semantic[:500]}")
        semantic_result = {
            "action": "create_event",
            "title": None,
            "description": None,
            "location": None
        }
    
    # Step 2: Extract time fields (start_time, end_time, all_day)
    prompt_time = PROMPT_TEMPLATE_CREATE_TIME.replace("{{CURRENT_DATE}}", anchors['current_date'])
    prompt_time = prompt_time.replace("{{TOMORROW}}", anchors['tomorrow'])
    prompt_time = prompt_time.replace("{{DAY_AFTER_TOMORROW}}", anchors['day_after_tomorrow'])
    prompt_time = prompt_time.replace("{{CURRENT_YEAR}}", anchors['current_year'])
    prompt_time = prompt_time.replace("{{USER_INPUT}}", user_input)
    
    response_time = None
    try:
        # Use fine-tuned time parser model for time extraction
        response_time = _call_ollama(prompt_time, model=MODEL_TIME_PARSER)
        time_result = _parse_json_from_llm_response(response_time, logger)
    except Exception as e:
        logger.error(f"Error extracting time fields: {str(e)}")
        # Log the raw response for debugging if we have it
        if response_time:
            logger.debug(f"Raw time response: {response_time[:500]}")
        time_result = {
            "start_time": None,
            "end_time": None,
            "all_day": None
        }
    
    # Merge results
    result = {
        "action": "create_event",
        "title": semantic_result.get("title"),
        "description": semantic_result.get("description"),
        "location": semantic_result.get("location"),
        "start_time": time_result.get("start_time"),
        "end_time": time_result.get("end_time"),
        "all_day": time_result.get("all_day")
    }
    
    # Normalize empty strings to null
    for key in ["title", "description", "location", "start_time", "end_time"]:
        if key in result and isinstance(result[key], str) and not result[key].strip():
            result[key] = None
    
    # Normalize all_day to boolean or None
    if "all_day" in result:
        if result["all_day"] is None or result["all_day"] == "":
            result["all_day"] = None
        else:
            result["all_day"] = bool(result["all_day"])
    else:
        result["all_day"] = None
    
    return result


def extract_fields_update_event(user_input: str) -> Dict[str, Any]:
    """Extract fields for update_event intent."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Format prompt template with variables (new prompt only uses USER_INPUT)
    prompt = PROMPT_TEMPLATE_UPDATE.replace("{{USER_INPUT}}", user_input)
    
    try:
        # Use entity parser for extracting event identifier and updated fields
        response_text = _call_ollama(prompt, model=MODEL_ENTITY_PARSER)
        result = _parse_json_from_llm_response(response_text, logger)
        
        # Ensure action field is set
        if "action" not in result:
            result["action"] = "update_event"
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting update_event fields: {str(e)}")
        return {
            "action": "update_event",
            "event_identifier": None,
            "updated_fields": {}
        }


def extract_fields_delete_event(user_input: str) -> Dict[str, Any]:
    """Extract fields for delete_event intent."""
    import logging
    logger = logging.getLogger(__name__)
    
    # Format prompt template with variables (new prompt only uses USER_INPUT)
    prompt = PROMPT_TEMPLATE_DELETE.replace("{{USER_INPUT}}", user_input)
    
    try:
        # Use entity parser for extracting event identifier
        response_text = _call_ollama(prompt, model=MODEL_ENTITY_PARSER)
        result = _parse_json_from_llm_response(response_text, logger)
        
        # Ensure action field is set
        if "action" not in result:
            result["action"] = "delete_event"
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting delete_event fields: {str(e)}")
        return {
            "action": "delete_event",
            "event_identifier": None
        }


def extract_fields_list_events(user_input: str) -> Dict[str, Any]:
    """Extract fields for list_events intent."""
    import logging
    logger = logging.getLogger(__name__)
    
    anchors = _get_temporal_anchors()
    
    # Format prompt template with variables
    prompt = PROMPT_TEMPLATE_LIST.replace("{{CURRENT_DATE}}", anchors['current_date'])
    prompt = prompt.replace("{{TOMORROW}}", anchors['tomorrow'])
    prompt = prompt.replace("{{USER_INPUT}}", user_input)
    
    try:
        # Use time parser for extracting time range for listing events
        response_text = _call_ollama(prompt, model=MODEL_TIME_PARSER)
        result = _parse_json_from_llm_response(response_text, logger)
        
        # Ensure action field is set
        if "action" not in result:
            result["action"] = "list_events"
        
        return result
        
    except Exception as e:
        logger.error(f"Error extracting list_events fields: {str(e)}")
        return {
            "action": "list_events",
            "start_time": None,
            "end_time": None
        }


def extract_fields(intent: str, user_input: str) -> Dict[str, Any]:
    """
    Dispatch to appropriate intent-specific extractor.
    
    Args:
        intent: The locked intent
        user_input: User's text input
        
    Returns:
        Dictionary with extracted fields
    """
    if intent == "create_event":
        return extract_fields_create_event(user_input)
    elif intent == "update_event":
        return extract_fields_update_event(user_input)
    elif intent == "delete_event":
        return extract_fields_delete_event(user_input)
    elif intent == "list_events":
        return extract_fields_list_events(user_input)
    else:
        return {
            "action": intent,
            "error": "Unknown intent"
        }

