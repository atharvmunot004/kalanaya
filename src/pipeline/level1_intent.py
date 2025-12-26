"""Level 1: Intent Classification - Classify intent only, no field extraction."""

import requests
import json
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
MODEL = "kalanaya-intent-parser"  # Fine-tuned LoRA adapter for intent classification

# Load prompt template
_PROJECT_ROOT = Path(__file__).parent.parent.parent
_PROMPT_PATH = _PROJECT_ROOT / "prompts" / "level1_intent.llama.txt"
with open(_PROMPT_PATH, "r", encoding="utf-8") as f:
    PROMPT_TEMPLATE = f.read()


def _get_temporal_anchors() -> Dict[str, str]:
    """Get current date/time information for prompts."""
    now = datetime.now(TZ)
    return {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "current_datetime_iso": now.isoformat(),
        "current_day_name": now.strftime("%A"),
        "current_date_readable": now.strftime("%B %d, %Y"),
    }


def _call_ollama(prompt: str) -> str:
    """Call Ollama API with the given prompt."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
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


def classify_intent(user_input: str) -> Dict[str, Any]:
    """
    Level 1: Classify user intent into exactly ONE of the supported intents.
    
    Args:
        user_input: User's text input
        
    Returns:
        Dictionary with:
            - intent: string (one of: create_event, update_event, delete_event, list_events, unknown)
            - confidence: float (0.0 to 1.0)
            - reasoning: string (short explanation)
    """
    # Format prompt template with variables (new prompt only uses USER_INPUT)
    prompt = PROMPT_TEMPLATE.replace("{{USER_INPUT}}", user_input)
    
    try:
        response_text = _call_ollama(prompt)
        
        # Parse JSON response
        response_text = response_text.strip()
        # Remove markdown code fences if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)
        
        # Try to extract JSON if it's embedded in text
        if "{" in response_text and "}" in response_text:
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx]
        
        result = json.loads(response_text)
        
        # Validate result structure (code-based validation)
        if "intent" not in result:
            raise ValueError("Missing 'intent' field in response")
        if "confidence" not in result:
            raise ValueError("Missing 'confidence' field in response")
        
        # Ensure intent is valid
        valid_intents = ["create_event", "update_event", "delete_event", "list_events", "unknown"]
        if result["intent"] not in valid_intents:
            result["intent"] = "unknown"
            result["confidence"] = 0.0
            result["ambiguous"] = True
        
        # Ensure confidence is in valid range
        confidence = float(result.get("confidence", 0.0))
        result["confidence"] = max(0.0, min(1.0, confidence))
        
        # Enforce ambiguous flag based on confidence threshold (code-based rule)
        if "ambiguous" not in result:
            result["ambiguous"] = confidence < 0.75
        else:
            # If confidence < 0.75, ambiguous must be true (enforce consistency)
            if confidence < 0.75:
                result["ambiguous"] = True
        
        return result
        
    except json.JSONDecodeError as e:
        # Log the raw response for debugging
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"JSON decode error in intent classification. Raw response: {response_text[:200]}")
        # Return unknown intent on JSON error
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "ambiguous": True
        }
    except Exception as e:
        # Return unknown intent on error
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error during intent classification: {str(e)}")
        return {
            "intent": "unknown",
            "confidence": 0.0,
            "ambiguous": True
        }

