"""Router module for handling intents and executing calendar actions."""

from typing import Dict, Any, Optional
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.actions import (
    get_calendar_service,
    create_event,
    update_event,
    delete_event,
    list_events,
    find_events,
)
from src.utils.validators import validate_event_params
from src.utils.logging import setup_logger

# Calculate logs directory
_current_file = Path(__file__).resolve()
if 'site-packages' in str(_current_file) or 'dist-packages' in str(_current_file):
    import os
    _logs_dir = Path(os.getcwd()) / "logs"
else:
    _PROJECT_ROOT = _current_file.parent.parent.parent
    _logs_dir = _PROJECT_ROOT / "logs"

# Set up logger
_logs_dir.mkdir(exist_ok=True)
logger = setup_logger("router", log_file=_logs_dir / "router.log")


def _find_event_by_title(
    service,
    title: str,
    time_min: Optional[str] = None,
    time_max: Optional[str] = None,
) -> Optional[str]:
    """
    Find an event ID by title. Returns the first matching event ID or None.
    
    Args:
        service: Google Calendar service
        title: Event title to search for
        time_min: Optional start time for search window
        time_max: Optional end time for search window
        
    Returns:
        Event ID if found, None otherwise
    """
    if not title or not title.strip():
        logger.debug("Empty title provided for event search")
        return None
    
    logger.debug(f"Searching for event: title='{title}', time_min={time_min}, time_max={time_max}")
    
    # Search for events with matching title
    result = find_events(
        service,
        title_contains=title,
        time_min=time_min,
        time_max=time_max,
        max_results=10,
    )
    
    if result.get("status") == "success" and result.get("events"):
        # Return the first matching event ID
        events = result.get("events", [])
        logger.debug(f"Found {len(events)} potential matches")
        for event in events:
            event_title = event.get("summary", "").strip()
            if title.lower() in event_title.lower() or event_title.lower() in title.lower():
                event_id = event.get("id")
                logger.debug(f"Matched event: id={event_id}, title='{event_title}'")
                return event_id
    
    logger.debug(f"No matching event found for title: '{title}'")
    return None


def _build_update_dict(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build an update dictionary from payload for updating an event.
    
    Args:
        payload: Payload dictionary from pipeline
        
    Returns:
        Dictionary with fields to update
    """
    updates: Dict[str, Any] = {}
    
    if payload.get("title"):
        updates["summary"] = payload["title"]
    
    if payload.get("start_time"):
        updates["start"] = {
            "dateTime": payload["start_time"],
            "timeZone": "Asia/Kolkata",
        }
    
    if payload.get("end_time"):
        updates["end"] = {
            "dateTime": payload["end_time"],
            "timeZone": "Asia/Kolkata",
        }
    elif payload.get("start_time") and not payload.get("end_time"):
        # If only start_time is provided, set end_time to start_time + 1 hour
        try:
            start_dt = datetime.fromisoformat(payload["start_time"].replace("Z", "+00:00"))
            end_dt = start_dt + timedelta(hours=1)
            updates["end"] = {
                "dateTime": end_dt.isoformat(),
                "timeZone": "Asia/Kolkata",
            }
        except (ValueError, AttributeError):
            pass
    
    if payload.get("description"):
        updates["description"] = payload["description"]
    
    return updates


def route(pipeline_result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Route a pipeline result to the appropriate calendar action.
    
    The pipeline result follows the final_output_contract:
    - success_schema: {status: "success", action: string, payload: object, confidence: float}
    - failure_schema: {status: "failure", reason: string, intent: string, confidence: float}
    
    Args:
        pipeline_result: Result from multi-level pipeline
        
    Returns:
        Dictionary with action result
    """
    status = pipeline_result.get("status")
    action = pipeline_result.get("action", "none")
    confidence = pipeline_result.get("confidence", 0.0)
    
    logger.info(f"Routing pipeline result: status={status}, action={action}, confidence={confidence}")
    
    # Handle failure status
    if status == "failure":
        logger.warning(f"Pipeline failed: {pipeline_result.get('reason')}")
        return {
            "status": "error",
            "action": action,
            "error": pipeline_result.get("reason", "Unknown error"),
            "confidence": confidence,
        }
    
    # Handle success status
    if status != "success":
        logger.error(f"Unexpected pipeline status: {status}")
        return {
            "status": "error",
            "action": action,
            "error": f"Unexpected pipeline status: {status}",
            "confidence": confidence,
        }
    
    # Get payload
    payload = pipeline_result.get("payload", {})
    
    # Get calendar service
    try:
        logger.debug("Getting calendar service")
        service = get_calendar_service()
        logger.debug("Calendar service obtained successfully")
    except Exception as e:
        logger.error(f"Failed to get calendar service: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "action": action,
            "error": f"Failed to get calendar service: {str(e)}",
            "confidence": confidence,
        }
    
    # Route to appropriate action
    if action == "create_event":
        title = payload.get("title", "").strip()
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        description = payload.get("description", "").strip()
        location = payload.get("location", "").strip()
        all_day = payload.get("all_day")
        
        logger.info(f"Creating event: title='{title}', start_time={start_time}, end_time={end_time}, all_day={all_day}")
        
        # Safety check: Required fields must be present (should already be validated by pipeline)
        if not title:
            logger.warning("SAFETY CHECK FAILED: Create event - title is required")
            return {
                "status": "error",
                "action": "create_event",
                "error": "Title is required for creating an event",
                "confidence": confidence,
            }
        
        if not start_time:
            logger.warning("SAFETY CHECK FAILED: Create event - start_time is required")
            return {
                "status": "error",
                "action": "create_event",
                "error": "Start time is required for creating an event",
                "confidence": confidence,
            }
        
        # Validate event params (datetime format, logic)
        # Skip validation for all-day events as they use date format, not datetime
        if not all_day:
            is_valid, error_msg = validate_event_params(title, start_time, end_time)
            if not is_valid:
                logger.warning(f"SAFETY CHECK FAILED: Create event validation - {error_msg}")
                return {
                    "status": "error",
                    "action": "create_event",
                    "error": f"Invalid event parameters: {error_msg}",
                    "confidence": confidence,
                }
        
        try:
            result = create_event(
                service,
                title=title,
                start_time=start_time,
                end_time=end_time,
                description=description,
                location=location,
                all_day=all_day,
            )
            result["confidence"] = confidence
            if result.get("status") == "success":
                logger.info(f"Event created successfully: event_id={result.get('event_id')}")
            else:
                logger.error(f"Event creation failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"Exception during event creation: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "action": "create_event",
                "error": f"Exception during event creation: {str(e)}",
                "confidence": confidence,
            }
    
    elif action == "update_event":
        title = payload.get("title", "").strip()
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        description = payload.get("description", "").strip()
        
        logger.info(f"Updating event: title='{title}', start_time={start_time}")
        
        # Safety check: Title required to find event
        if not title:
            logger.warning("SAFETY CHECK FAILED: Update event - title is required")
            return {
                "status": "error",
                "action": "update_event",
                "error": "Title is required to find the event to update",
                "confidence": confidence,
            }
        
        # Find event by title
        time_min = None
        time_max = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                time_min = (start_dt - timedelta(days=7)).isoformat()
                time_max = (start_dt + timedelta(days=7)).isoformat()
                logger.debug(f"Search window: {time_min} to {time_max}")
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid start_time format for search window: {e}")
        
        event_id = _find_event_by_title(service, title, time_min=time_min, time_max=time_max)
        
        if not event_id:
            logger.warning(f"Event not found for update: title='{title}'")
            return {
                "status": "error",
                "action": "update_event",
                "error": f"Event not found: {title}",
                "confidence": confidence,
            }
        
        logger.debug(f"Found event to update: event_id={event_id}")
        
        # Build update payload
        update_payload = {
            "title": title,
            "start_time": start_time,
            "end_time": end_time,
            "description": description,
        }
        updates = _build_update_dict(update_payload)
        
        if not updates:
            logger.warning("No fields to update")
            return {
                "status": "error",
                "action": "update_event",
                "error": "No fields to update",
                "confidence": confidence,
            }
        
        logger.debug(f"Update payload: {updates}")
        try:
            result = update_event(service, event_id, updates)
            result["confidence"] = confidence
            if result.get("status") == "success":
                logger.info(f"Event updated successfully: event_id={event_id}")
            else:
                logger.error(f"Event update failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"Exception during event update: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "action": "update_event",
                "error": f"Exception during event update: {str(e)}",
                "confidence": confidence,
            }
    
    elif action == "delete_event":
        title = payload.get("title", "").strip()
        start_time = payload.get("start_time")
        
        logger.info(f"Deleting event: title='{title}', start_time={start_time}")
        
        # Safety check: Title required to find event
        if not title:
            logger.warning("SAFETY CHECK FAILED: Delete event - title is required")
            return {
                "status": "error",
                "action": "delete_event",
                "error": "Title is required to find the event to delete",
                "confidence": confidence,
            }
        
        # Find event by title
        time_min = None
        time_max = None
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
                time_min = (start_dt - timedelta(days=7)).isoformat()
                time_max = (start_dt + timedelta(days=7)).isoformat()
                logger.debug(f"Search window: {time_min} to {time_max}")
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid start_time format for search window: {e}")
        
        event_id = _find_event_by_title(service, title, time_min=time_min, time_max=time_max)
        
        if not event_id:
            logger.warning(f"Event not found for deletion: title='{title}'")
            return {
                "status": "error",
                "action": "delete_event",
                "error": f"Event not found: {title}",
                "confidence": confidence,
            }
        
        logger.debug(f"Found event to delete: event_id={event_id}")
        try:
            result = delete_event(service, event_id)
            result["confidence"] = confidence
            if result.get("status") == "success":
                logger.info(f"Event deleted successfully: event_id={event_id}")
            else:
                logger.error(f"Event deletion failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"Exception during event deletion: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "action": "delete_event",
                "error": f"Exception during event deletion: {str(e)}",
                "confidence": confidence,
            }
    
    elif action == "list_events":
        start_time = payload.get("start_time")
        end_time = payload.get("end_time")
        title = payload.get("title", "").strip()
        
        logger.info(f"Listing events: start_time={start_time}, end_time={end_time}, title='{title}'")
        
        time_min = start_time
        time_max = end_time
        
        # If start_time is provided but not end_time, set end_time to start_time + 24 hours
        if time_min and not time_max:
            try:
                start_dt = datetime.fromisoformat(time_min.replace("Z", "+00:00"))
                time_max_dt = start_dt + timedelta(hours=24)
                time_max = time_max_dt.isoformat()
                logger.debug(f"Time window: {time_min} to {time_max}")
            except (ValueError, AttributeError) as e:
                logger.warning(f"Invalid start_time format: {e}")
        
        # If title is provided, use it as a query
        query = title if title else None
        
        try:
            result = list_events(
                service,
                time_min=time_min,
                time_max=time_max,
                query=query,
                max_results=10,
            )
            result["confidence"] = confidence
            if result.get("status") == "success":
                count = result.get("count", 0)
                logger.info(f"Listed {count} events successfully")
            else:
                logger.error(f"Event listing failed: {result.get('error')}")
            return result
        except Exception as e:
            logger.error(f"Exception during event listing: {str(e)}", exc_info=True)
            return {
                "status": "error",
                "action": "list_events",
                "error": f"Exception during event listing: {str(e)}",
                "confidence": confidence,
            }
    
    else:
        logger.error(f"Unknown action: {action}")
        return {
            "status": "error",
            "action": action,
            "error": f"Unknown action: {action}",
            "confidence": confidence,
        }
