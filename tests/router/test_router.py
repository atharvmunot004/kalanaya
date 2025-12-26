"""Unit tests for router module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.router.router import route, _find_event_by_title, _build_update_dict


class TestRoute:
    """Test the main route function."""
    
    @patch('src.router.router.get_calendar_service')
    @patch('src.router.router.create_event')
    def test_route_create_event(self, mock_create, mock_get_service, mock_calendar_service):
        """Test routing create_event action."""
        mock_get_service.return_value = mock_calendar_service
        mock_create.return_value = {
            "status": "success",
            "action": "create_event",
            "event_id": "test123",
            "html_link": "https://calendar.google.com/event?eid=test123"
        }
        
        pipeline_result = {
            "status": "success",
            "action": "create_event",
            "payload": {
                "title": "Test Meeting",
                "start_time": "2025-12-20T10:00:00+05:30",
                "end_time": "2025-12-20T11:00:00+05:30"
            },
            "confidence": 0.9
        }
        
        result = route(pipeline_result)
        
        assert result["status"] == "success"
        assert result["action"] == "create_event"
        assert "confidence" in result
    
    def test_route_failure_status(self):
        """Test routing failure status."""
        pipeline_result = {
            "status": "failure",
            "reason": "Validation failed",
            "intent": "create_event",
            "confidence": 0.5
        }
        
        result = route(pipeline_result)
        
        assert result["status"] == "error"
        assert "error" in result
        assert result["error"] == "Validation failed"
    
    @patch('src.router.router.get_calendar_service')
    @patch('src.router.router.list_events')
    def test_route_list_events(self, mock_list, mock_get_service, mock_calendar_service):
        """Test routing list_events action."""
        mock_get_service.return_value = mock_calendar_service
        mock_list.return_value = {
            "status": "success",
            "action": "list_events",
            "events": [],
            "count": 0
        }
        
        pipeline_result = {
            "status": "success",
            "action": "list_events",
            "payload": {
                "start_time": "2025-12-20T00:00:00+05:30",
                "end_time": "2025-12-21T00:00:00+05:30"
            },
            "confidence": 0.9
        }
        
        result = route(pipeline_result)
        
        assert result["status"] == "success"
        assert result["action"] == "list_events"
    
    @patch('src.router.router.get_calendar_service')
    def test_route_missing_title_create(self, mock_get_service, mock_calendar_service):
        """Test routing create_event without title."""
        mock_get_service.return_value = mock_calendar_service
        
        pipeline_result = {
            "status": "success",
            "action": "create_event",
            "payload": {
                "start_time": "2025-12-20T10:00:00+05:30"
            },
            "confidence": 0.9
        }
        
        result = route(pipeline_result)
        
        assert result["status"] == "error"
        assert "Title is required" in result["error"]


class TestFindEventByTitle:
    """Test _find_event_by_title function."""
    
    @patch('src.router.router.find_events')
    def test_find_event_success(self, mock_find_events):
        """Test finding event by title."""
        mock_find_events.return_value = {
            "status": "success",
            "events": [
                {
                    "id": "event123",
                    "summary": "Test Meeting",
                    "start": {"dateTime": "2025-12-20T10:00:00+05:30"},
                    "end": {"dateTime": "2025-12-20T11:00:00+05:30"}
                }
            ]
        }
        
        service = MagicMock()
        event_id = _find_event_by_title(service, "Test Meeting")
        
        assert event_id == "event123"
    
    @patch('src.router.router.find_events')
    def test_find_event_not_found(self, mock_find_events):
        """Test when event is not found."""
        mock_find_events.return_value = {
            "status": "success",
            "events": []
        }
        
        service = MagicMock()
        event_id = _find_event_by_title(service, "Non-existent Event")
        
        assert event_id is None
    
    def test_find_event_empty_title(self):
        """Test with empty title."""
        service = MagicMock()
        event_id = _find_event_by_title(service, "")
        
        assert event_id is None


class TestBuildUpdateDict:
    """Test _build_update_dict function."""
    
    def test_build_update_dict_title(self):
        """Test building update dict with title."""
        payload = {
            "title": "Updated Title"
        }
        
        updates = _build_update_dict(payload)
        
        assert "summary" in updates
        assert updates["summary"] == "Updated Title"
    
    def test_build_update_dict_time(self):
        """Test building update dict with time."""
        payload = {
            "start_time": "2025-12-20T14:00:00+05:30",
            "end_time": "2025-12-20T15:00:00+05:30"
        }
        
        updates = _build_update_dict(payload)
        
        assert "start" in updates
        assert "end" in updates
        assert updates["start"]["dateTime"] == "2025-12-20T14:00:00+05:30"
    
    def test_build_update_dict_description(self):
        """Test building update dict with description."""
        payload = {
            "description": "Updated description"
        }
        
        updates = _build_update_dict(payload)
        
        assert "description" in updates
        assert updates["description"] == "Updated description"

