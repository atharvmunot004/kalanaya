"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture
def mock_ollama_response():
    """Mock Ollama API response."""
    def _mock_response(json_data):
        mock = Mock()
        mock.json.return_value = json_data
        mock.raise_for_status = Mock()
        return mock
    return _mock_response


@pytest.fixture
def mock_calendar_service():
    """Mock Google Calendar service."""
    service = MagicMock()
    events = MagicMock()
    service.events.return_value = events
    
    # Mock insert (create)
    insert_mock = MagicMock()
    insert_mock.execute.return_value = {
        "id": "test_event_id_123",
        "htmlLink": "https://calendar.google.com/event?eid=test123",
        "summary": "Test Event",
        "start": {"dateTime": "2025-12-20T10:00:00+05:30"},
        "end": {"dateTime": "2025-12-20T11:00:00+05:30"}
    }
    events.insert.return_value = insert_mock
    
    # Mock list
    list_mock = MagicMock()
    list_mock.execute.return_value = {
        "items": [
            {
                "id": "event1",
                "summary": "Test Event 1",
                "start": {"dateTime": "2025-12-20T10:00:00+05:30"},
                "end": {"dateTime": "2025-12-20T11:00:00+05:30"},
                "htmlLink": "https://calendar.google.com/event?eid=event1",
                "status": "confirmed"
            }
        ]
    }
    events.list.return_value = list_mock
    
    # Mock patch (update)
    patch_mock = MagicMock()
    patch_mock.execute.return_value = {
        "id": "test_event_id_123",
        "htmlLink": "https://calendar.google.com/event?eid=test123",
        "summary": "Updated Event",
        "start": {"dateTime": "2025-12-20T10:00:00+05:30"},
        "end": {"dateTime": "2025-12-20T11:00:00+05:30"}
    }
    events.patch.return_value = patch_mock
    
    # Mock delete
    delete_mock = MagicMock()
    delete_mock.execute.return_value = None
    events.delete.return_value = delete_mock
    
    return service


@pytest.fixture
def sample_create_event_fields():
    """Sample extracted fields for create_event."""
    return {
        "action": "create_event",
        "title": "Test Meeting",
        "start_time": "2025-12-20T10:00:00+05:30",
        "end_time": "2025-12-20T11:00:00+05:30",
        "description": "Test description",
        "location": "Test Location",
        "all_day": False
    }


@pytest.fixture
def sample_update_event_fields():
    """Sample extracted fields for update_event."""
    return {
        "action": "update_event",
        "event_identifier": "Test Meeting",
        "updated_fields": {
            "title": "Updated Meeting",
            "start_time": "2025-12-20T14:00:00+05:30"
        }
    }


@pytest.fixture
def sample_delete_event_fields():
    """Sample extracted fields for delete_event."""
    return {
        "action": "delete_event",
        "event_identifier": "Test Meeting"
    }


@pytest.fixture
def sample_list_events_fields():
    """Sample extracted fields for list_events."""
    return {
        "action": "list_events",
        "start_time": "2025-12-20T00:00:00+05:30",
        "end_time": "2025-12-21T00:00:00+05:30"
    }

