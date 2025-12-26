"""Validation utilities for calendar intents and actions."""

from typing import Dict, Any, Optional, Tuple
from datetime import datetime

def validate_intent(intent: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate an intent dictionary.
    
    Args:
        intent: Intent dictionary from the intent engine
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["action", "confidence"]
    for field in required_fields:
        if field not in intent:
            return False, f"Missing required field: {field}"
    
    # Validate action
    valid_actions = ["create_event", "update_event", "delete_event", "list_events", "none"]
    if intent["action"] not in valid_actions:
        return False, f"Invalid action: {intent['action']}. Must be one of {valid_actions}"
    
    # Validate confidence
    confidence = intent.get("confidence", 0.0)
    if not isinstance(confidence, (int, float)) or not (0.0 <= confidence <= 1.0):
        return False, f"Invalid confidence: {confidence}. Must be between 0.0 and 1.0"
    
    # Validate timestamps if provided
    for time_field in ["start_time", "end_time"]:
        if time_field in intent and intent[time_field] is not None:
            time_str = intent[time_field]
            try:
                # Try parsing as RFC3339
                datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                return False, f"Invalid {time_field} format: {time_str}. Must be RFC3339"
    
    return True, None


def validate_event_params(title: str, start_time: str, end_time: Optional[str] = None) -> Tuple[bool, Optional[str]]:
    """
    Validate event creation parameters.
    
    Args:
        title: Event title
        start_time: Start time in RFC3339 format
        end_time: Optional end time in RFC3339 format
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not title or not title.strip():
        return False, "Title cannot be empty"
    
    try:
        start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return False, f"Invalid start_time format: {start_time}. Must be RFC3339"
    
    if end_time:
        try:
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        except (ValueError, AttributeError):
            return False, f"Invalid end_time format: {end_time}. Must be RFC3339"
        
        if end_dt <= start_dt:
            return False, "end_time must be after start_time"
    
    return True, None

