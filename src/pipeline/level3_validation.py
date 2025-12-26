"""Level 3: Deterministic Code-Based Validation - Validate extracted fields without LLM."""

import re
from datetime import datetime
from typing import Dict, Any, List, Optional

# ISO 8601 datetime pattern with timezone
ISO_8601_PATTERN = re.compile(
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$'
)


def _validate_iso8601_datetime(value: str) -> bool:
    """Validate ISO 8601 datetime format with timezone."""
    if not isinstance(value, str):
        return False
    return bool(ISO_8601_PATTERN.match(value))


def _parse_datetime(value: str) -> Optional[datetime]:
    """Parse ISO 8601 datetime string."""
    try:
        # Try parsing with timezone
        if '+' in value or value.count('-') > 2:
            # Has timezone info
            return datetime.fromisoformat(value.replace('Z', '+00:00'))
        else:
            # No timezone, assume local
            return datetime.fromisoformat(value)
    except (ValueError, AttributeError):
        return None


def _validate_create_event(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate create_event fields deterministically.
    
    Required:
    - title (non-null, non-empty string)
    
    Optional but validated if present:
    - start_time (ISO 8601 format)
    - end_time (ISO 8601 format, must be after start_time if both present)
    - all_day (boolean, must be consistent with time presence)
    - description (string or null)
    - location (string or null)
    """
    errors: List[str] = []
    missing_fields: List[str] = []
    
    # Required field: title
    title = extracted_fields.get("title")
    if not title or (isinstance(title, str) and not title.strip()):
        missing_fields.append("title")
        errors.append("title is required and cannot be empty")
    
    # Validate start_time if present
    start_time = extracted_fields.get("start_time")
    if start_time is not None:
        if not isinstance(start_time, str):
            errors.append("start_time must be a string")
        elif not _validate_iso8601_datetime(start_time):
            errors.append("start_time must be in ISO 8601 format with timezone (e.g., 2024-01-15T10:00:00+05:30)")
        else:
            # Validate it can be parsed
            parsed_start = _parse_datetime(start_time)
            if parsed_start is None:
                errors.append("start_time is not a valid datetime")
    
    # Validate end_time if present
    end_time = extracted_fields.get("end_time")
    if end_time is not None:
        if not isinstance(end_time, str):
            errors.append("end_time must be a string")
        elif not _validate_iso8601_datetime(end_time):
            errors.append("end_time must be in ISO 8601 format with timezone (e.g., 2024-01-15T11:00:00+05:30)")
        else:
            # Validate it can be parsed
            parsed_end = _parse_datetime(end_time)
            if parsed_end is None:
                errors.append("end_time is not a valid datetime")
    
    # Validate end_time > start_time if both present
    if start_time and end_time:
        parsed_start = _parse_datetime(start_time)
        parsed_end = _parse_datetime(end_time)
        if parsed_start and parsed_end:
            if parsed_end <= parsed_start:
                errors.append("end_time must be after start_time")
    
    # Validate all_day consistency
    all_day = extracted_fields.get("all_day")
    if all_day is not None:
        if not isinstance(all_day, bool):
            errors.append("all_day must be a boolean")
        else:
            # If all_day is True, times should not have time components (only date)
            if all_day and start_time:
                if 'T' in start_time and ':' in start_time.split('T')[1]:
                    errors.append("all_day=true but start_time contains time component")
            # If all_day is False, times should have time components
            if all_day is False and start_time:
                if 'T' not in start_time or ':' not in start_time.split('T')[1]:
                    errors.append("all_day=false but start_time does not contain time component")
    
    # Validate description (optional, but if present should be string)
    description = extracted_fields.get("description")
    if description is not None and not isinstance(description, str):
        errors.append("description must be a string or null")
    
    # Validate location (optional, but if present should be string)
    location = extracted_fields.get("location")
    if location is not None and not isinstance(location, str):
        errors.append("location must be a string or null")
    
    is_valid = len(missing_fields) == 0 and len(errors) == 0
    retry_required = len(missing_fields) > 0  # Only retry if required fields are missing
    
    return {
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "errors": errors,
        "retry_required": retry_required
    }


def _validate_update_event(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate update_event fields deterministically.
    
    Required:
    - event_identifier (non-null, non-empty string)
    - updated_fields (dict with at least one non-null field)
    """
    errors: List[str] = []
    missing_fields: List[str] = []
    
    # Required: event_identifier
    event_identifier = extracted_fields.get("event_identifier")
    if not event_identifier or (isinstance(event_identifier, str) and not event_identifier.strip()):
        missing_fields.append("event_identifier")
        errors.append("event_identifier is required to identify which event to update")
    
    # Required: updated_fields with at least one non-null field
    updated_fields = extracted_fields.get("updated_fields", {})
    if not isinstance(updated_fields, dict):
        missing_fields.append("updated_fields")
        errors.append("updated_fields must be a dictionary")
    else:
        # Check if at least one field is non-null
        has_any_field = False
        for key, value in updated_fields.items():
            if value is not None:
                if isinstance(value, str) and value.strip():
                    has_any_field = True
                    break
                elif not isinstance(value, str):
                    has_any_field = True
                    break
        
        if not has_any_field:
            missing_fields.append("updated_fields")
            errors.append("updated_fields must contain at least one non-null field to update")
        
        # Validate time fields if present
        if "start_time" in updated_fields and updated_fields["start_time"] is not None:
            start_time = updated_fields["start_time"]
            if not isinstance(start_time, str):
                errors.append("updated_fields.start_time must be a string")
            elif not _validate_iso8601_datetime(start_time):
                errors.append("updated_fields.start_time must be in ISO 8601 format with timezone")
            else:
                parsed_start = _parse_datetime(start_time)
                if parsed_start is None:
                    errors.append("updated_fields.start_time is not a valid datetime")
        
        if "end_time" in updated_fields and updated_fields["end_time"] is not None:
            end_time = updated_fields["end_time"]
            if not isinstance(end_time, str):
                errors.append("updated_fields.end_time must be a string")
            elif not _validate_iso8601_datetime(end_time):
                errors.append("updated_fields.end_time must be in ISO 8601 format with timezone")
            else:
                parsed_end = _parse_datetime(end_time)
                if parsed_end is None:
                    errors.append("updated_fields.end_time is not a valid datetime")
        
        # Validate end_time > start_time if both present
        if (updated_fields.get("start_time") and updated_fields.get("end_time")):
            parsed_start = _parse_datetime(updated_fields["start_time"])
            parsed_end = _parse_datetime(updated_fields["end_time"])
            if parsed_start and parsed_end and parsed_end <= parsed_start:
                errors.append("updated_fields.end_time must be after updated_fields.start_time")
    
    is_valid = len(missing_fields) == 0 and len(errors) == 0
    retry_required = len(missing_fields) > 0
    
    return {
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "errors": errors,
        "retry_required": retry_required
    }


def _validate_delete_event(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate delete_event fields deterministically.
    
    Required:
    - event_identifier (non-null, non-empty string)
    """
    errors: List[str] = []
    missing_fields: List[str] = []
    
    # Required: event_identifier
    event_identifier = extracted_fields.get("event_identifier")
    if not event_identifier or (isinstance(event_identifier, str) and not event_identifier.strip()):
        missing_fields.append("event_identifier")
        errors.append("event_identifier is required to identify which event to delete")
    
    is_valid = len(missing_fields) == 0 and len(errors) == 0
    retry_required = len(missing_fields) > 0
    
    return {
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "errors": errors,
        "retry_required": retry_required
    }


def _validate_list_events(extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate list_events fields deterministically.
    
    All fields are optional, but if present must be valid.
    """
    errors: List[str] = []
    missing_fields: List[str] = []  # No required fields for list_events
    
    # Validate start_time if present
    start_time = extracted_fields.get("start_time")
    if start_time is not None:
        if not isinstance(start_time, str):
            errors.append("start_time must be a string or null")
        elif not _validate_iso8601_datetime(start_time):
            errors.append("start_time must be in ISO 8601 format with timezone")
        else:
            parsed_start = _parse_datetime(start_time)
            if parsed_start is None:
                errors.append("start_time is not a valid datetime")
    
    # Validate end_time if present
    end_time = extracted_fields.get("end_time")
    if end_time is not None:
        if not isinstance(end_time, str):
            errors.append("end_time must be a string or null")
        elif not _validate_iso8601_datetime(end_time):
            errors.append("end_time must be in ISO 8601 format with timezone")
        else:
            parsed_end = _parse_datetime(end_time)
            if parsed_end is None:
                errors.append("end_time is not a valid datetime")
    
    # Validate end_time > start_time if both present
    if start_time and end_time:
        parsed_start = _parse_datetime(start_time)
        parsed_end = _parse_datetime(end_time)
        if parsed_start and parsed_end:
            if parsed_end <= parsed_start:
                errors.append("end_time must be after start_time")
    
    is_valid = len(errors) == 0
    retry_required = False  # No required fields, so no retry needed
    
    return {
        "is_valid": is_valid,
        "missing_fields": missing_fields,
        "errors": errors,
        "retry_required": retry_required
    }


def validate_fields(intent: str, extracted_fields: Dict[str, Any]) -> Dict[str, Any]:
    """
    Deterministic code-based validation of extracted fields.
    
    Args:
        intent: The locked intent
        extracted_fields: Fields extracted from Level 2
        
    Returns:
        Dictionary with:
            - is_valid: boolean
            - missing_fields: array of field names
            - errors: array of error messages
            - retry_required: boolean (true if required fields are missing)
    """
    if intent == "create_event":
        return _validate_create_event(extracted_fields)
    elif intent == "update_event":
        return _validate_update_event(extracted_fields)
    elif intent == "delete_event":
        return _validate_delete_event(extracted_fields)
    elif intent == "list_events":
        return _validate_list_events(extracted_fields)
    else:
        return {
            "is_valid": False,
            "missing_fields": [],
            "errors": [f"Unknown intent: {intent}"],
            "retry_required": False
        }
