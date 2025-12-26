"""Unit tests for calendar actions module."""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, MagicMock, patch
from googleapiclient.errors import HttpError
from src.actions.calendar_actions import (
    create_event,
    list_events,
    update_event,
    delete_event,
    find_events,
    _parse_rfc3339,
    _to_rfc3339,
    _ensure_rfc3339
)


class TestHelperFunctions:
    """Test helper functions."""
    
    def test_parse_rfc3339(self):
        """Test RFC3339 parsing."""
        dt_str = "2025-12-20T10:00:00+05:30"
        result = _parse_rfc3339(dt_str)
        assert isinstance(result, datetime)
        assert result.year == 2025
        assert result.month == 12
        assert result.day == 20
    
    def test_parse_rfc3339_with_z(self):
        """Test RFC3339 parsing with Z suffix."""
        dt_str = "2025-12-20T10:00:00Z"
        result = _parse_rfc3339(dt_str)
        assert isinstance(result, datetime)
        assert result.year == 2025
    
    def test_to_rfc3339(self):
        """Test RFC3339 conversion."""
        dt = datetime(2025, 12, 20, 10, 0, 0, tzinfo=timezone(timedelta(hours=5, minutes=30)))
        result = _to_rfc3339(dt)
        assert isinstance(result, str)
        assert "2025-12-20T10:00:00" in result


class TestCreateEvent:
    """Test create_event function."""
    
    def test_create_timed_event(self, mock_calendar_service):
        """Test creating a timed event."""
        result = create_event(
            mock_calendar_service,
            title="Test Event",
            start_time="2025-12-20T10:00:00+05:30",
            end_time="2025-12-20T11:00:00+05:30"
        )
        
        assert result["status"] == "success"
        assert result["action"] == "create_event"
        assert "event_id" in result
        assert "html_link" in result
    
    def test_create_event_without_end_time(self, mock_calendar_service):
        """Test creating event without end_time (should default to +1 hour)."""
        result = create_event(
            mock_calendar_service,
            title="Test Event",
            start_time="2025-12-20T10:00:00+05:30",
            end_time=None
        )
        
        assert result["status"] == "success"
        # Verify that end_time was set (service should have been called with end_time)
        mock_calendar_service.events().insert.assert_called_once()
    
    def test_create_all_day_event(self, mock_calendar_service):
        """Test creating an all-day event."""
        result = create_event(
            mock_calendar_service,
            title="Test Event",
            start_time="2025-12-20",
            end_time=None,
            all_day=True
        )
        
        assert result["status"] == "success"
        # Verify service was called with date format
        call_args = mock_calendar_service.events().insert.call_args
        body = call_args[1]["body"]
        assert "date" in body["start"]
        assert "date" in body["end"]
    
    def test_create_event_with_attendees(self, mock_calendar_service):
        """Test creating event with attendees."""
        result = create_event(
            mock_calendar_service,
            title="Test Event",
            start_time="2025-12-20T10:00:00+05:30",
            end_time="2025-12-20T11:00:00+05:30",
            attendees=["test@example.com"]
        )
        
        assert result["status"] == "success"
        call_args = mock_calendar_service.events().insert.call_args
        body = call_args[1]["body"]
        assert "attendees" in body


class TestListEvents:
    """Test list_events function."""
    
    def test_list_events_default_window(self, mock_calendar_service):
        """Test listing events with default time window."""
        result = list_events(mock_calendar_service)
        
        assert result["status"] == "success"
        assert result["action"] == "list_events"
        assert "events" in result
        assert "count" in result
    
    def test_list_events_with_time_range(self, mock_calendar_service):
        """Test listing events with specific time range."""
        result = list_events(
            mock_calendar_service,
            time_min="2025-12-20T00:00:00+05:30",
            time_max="2025-12-21T00:00:00+05:30"
        )
        
        assert result["status"] == "success"
        assert result["count"] >= 0
    
    def test_list_events_with_query(self, mock_calendar_service):
        """Test listing events with query."""
        result = list_events(
            mock_calendar_service,
            query="Meeting"
        )
        
        assert result["status"] == "success"


class TestUpdateEvent:
    """Test update_event function."""
    
    def test_update_event(self, mock_calendar_service):
        """Test updating an event."""
        updates = {
            "summary": "Updated Title"
        }
        
        result = update_event(
            mock_calendar_service,
            event_id="test_event_id_123",
            updates=updates
        )
        
        assert result["status"] == "success"
        assert result["action"] == "update_event"
        assert result["event_id"] == "test_event_id_123"
    
    def test_update_event_time(self, mock_calendar_service):
        """Test updating event time."""
        updates = {
            "start": {
                "dateTime": "2025-12-20T14:00:00+05:30",
                "timeZone": "Asia/Kolkata"
            }
        }
        
        result = update_event(
            mock_calendar_service,
            event_id="test_event_id_123",
            updates=updates
        )
        
        assert result["status"] == "success"


class TestDeleteEvent:
    """Test delete_event function."""
    
    def test_delete_event(self, mock_calendar_service):
        """Test deleting an event."""
        result = delete_event(
            mock_calendar_service,
            event_id="test_event_id_123"
        )
        
        assert result["status"] == "success"
        assert result["action"] == "delete_event"
        assert result["event_id"] == "test_event_id_123"
        mock_calendar_service.events().delete.assert_called_once()


class TestFindEvents:
    """Test find_events function."""
    
    def test_find_events_by_title(self, mock_calendar_service):
        """Test finding events by title."""
        result = find_events(
            mock_calendar_service,
            title_contains="Meeting"
        )
        
        assert result["status"] == "success"
        assert result["action"] == "list_events"

