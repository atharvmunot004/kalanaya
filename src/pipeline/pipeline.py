"""Multi-level prompt pipeline orchestrator."""

from typing import Dict, Any, Optional
import logging

from .level1_intent import classify_intent
from .level2_extraction import extract_fields
from .level3_validation import validate_fields

logger = logging.getLogger(__name__)

# Global configuration
CONFIDENCE_THRESHOLD = 0.75
# Removed MAX_VALIDATION_RETRIES - validation is now deterministic, no retries needed


# Removed _format_validation_feedback - validation is now deterministic code-based
# No LLM retries needed since validation doesn't use LLM


def process_user_input(user_input: str) -> Dict[str, Any]:
    """
    Process user input through the multi-level prompt pipeline.
    
    Pipeline flow:
    1. Level 1: Intent classification
    2. Level 2: Intent-specific field extraction
    3. Level 3: Validation
    4. Level 4: Retry logic (if validation fails)
    
    Args:
        user_input: User's text input
        
    Returns:
        Dictionary following final_output_contract:
            - success_schema: {status: "success", action: string, payload: object, confidence: float}
            - failure_schema: {status: "failure", reason: string, intent: string, confidence: float}
    """
    logger.info(f"Processing user input: {user_input[:100]}...")
    
    # ===== LEVEL 1: INTENT CLASSIFICATION =====
    logger.debug("Level 1: Intent classification")
    intent_result = classify_intent(user_input)
    
    intent = intent_result.get("intent", "unknown")
    confidence = float(intent_result.get("confidence", 0.0))
    ambiguous = intent_result.get("ambiguous", True)  # Default to ambiguous if not present
    
    logger.info(f"Intent classified: {intent} (confidence: {confidence}, ambiguous: {ambiguous})")
    
    # Code-based control flow: Check confidence threshold and ambiguous flag
    if confidence < CONFIDENCE_THRESHOLD or ambiguous:
        logger.warning(f"Low confidence ({confidence}) or ambiguous intent")
        return {
            "status": "failure",
            "reason": f"Intent confidence ({confidence}) below threshold ({CONFIDENCE_THRESHOLD}) or intent is ambiguous.",
            "intent": intent,
            "confidence": confidence
        }
    
    # Handle unknown intent
    if intent == "unknown":
        return {
            "status": "failure",
            "reason": "Could not determine user intent.",
            "intent": "unknown",
            "confidence": confidence
        }
    
    # ===== LEVEL 2: FIELD EXTRACTION =====
    logger.debug("Level 2: Field extraction")
    
    # Level 2: Extract fields (stateless, no validation feedback)
    extracted_fields = extract_fields(intent, user_input)
    
    logger.debug(f"Extracted fields: {extracted_fields}")
    
    # ===== LEVEL 3: DETERMINISTIC CODE-BASED VALIDATION =====
    logger.debug("Level 3: Code-based validation")
    validation_result = validate_fields(intent, extracted_fields)
    
    is_valid = validation_result.get("is_valid", False)
    retry_required = validation_result.get("retry_required", False)
    
    logger.info(f"Validation result: is_valid={is_valid}, retry_required={retry_required}")
    
    # Control flow: Code decides, not LLM
    # If validation fails, fail immediately (no LLM retries)
    if not is_valid:
        logger.warning("Validation failed")
        # Convert errors to strings
        errors = validation_result.get('errors', [])
        error_strings = []
        for e in errors:
            if isinstance(e, str):
                error_strings.append(e)
            elif isinstance(e, dict):
                # Handle common error dict formats
                if 'field' in e and 'error_type' in e:
                    error_strings.append(f"{e['field']}: {e['error_type']}")
                elif 'message' in e:
                    error_strings.append(e['message'])
                elif 'error' in e:
                    error_strings.append(e['error'])
                else:
                    error_strings.append(str(e))
            else:
                error_strings.append(str(e))
        
        # Build failure reason
        missing_fields = [str(f) for f in validation_result.get('missing_fields', [])]
        reason_parts = []
        if missing_fields:
            reason_parts.append(f"Missing required fields: {', '.join(missing_fields)}")
        if error_strings:
            reason_parts.append(f"Validation errors: {', '.join(error_strings)}")
        
        reason = "; ".join(reason_parts) if reason_parts else "Validation failed"
        
        return {
            "status": "failure",
            "reason": reason,
            "intent": intent,
            "confidence": confidence
        }
    
    # ===== SUCCESS OUTPUT =====
    # Convert extracted fields to payload format expected by router
    payload = _convert_to_payload(intent, extracted_fields)
    
    logger.info(f"Pipeline completed successfully: {intent}")
    
    return {
        "status": "success",
        "action": intent,
        "payload": payload,
        "confidence": confidence
    }


def _convert_to_payload(intent: str, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert extracted fields to payload format expected by router.
    
    Args:
        intent: The intent
        extracted_fields: Fields from Level 2
        
    Returns:
        Payload dictionary in format expected by router
    """
    if intent == "create_event":
        return {
            "title": extracted_fields.get("title") or "",
            "start_time": extracted_fields.get("start_time"),
            "end_time": extracted_fields.get("end_time"),
            "description": extracted_fields.get("description") or "",
            "location": extracted_fields.get("location") or "",
            "all_day": extracted_fields.get("all_day"),
        }
    elif intent == "update_event":
        # Convert update_event format to router format
        updated_fields = extracted_fields.get("updated_fields", {})
        return {
            "title": extracted_fields.get("event_identifier") or updated_fields.get("title") or "",
            "start_time": updated_fields.get("start_time"),
            "end_time": updated_fields.get("end_time"),
            "description": updated_fields.get("description") or "",
        }
    elif intent == "delete_event":
        return {
            "title": extracted_fields.get("event_identifier") or "",
            "start_time": None,  # Delete doesn't need start_time in router format
        }
    elif intent == "list_events":
        return {
            "start_time": extracted_fields.get("start_time"),
            "end_time": extracted_fields.get("end_time"),
            "title": "",  # List doesn't need title
        }
    else:
        return {}

