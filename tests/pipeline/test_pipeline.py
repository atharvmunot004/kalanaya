"""Unit tests for pipeline module."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.pipeline.pipeline import process_user_input, _convert_to_payload


class TestProcessUserInput:
    """Test the main pipeline processing function."""
    
    @patch('src.pipeline.pipeline.classify_intent')
    @patch('src.pipeline.pipeline.extract_fields')
    @patch('src.pipeline.pipeline.validate_fields')
    def test_successful_create_event(self, mock_validate, mock_extract, mock_classify):
        """Test successful processing of create_event intent."""
        # Mock Level 1: Intent classification
        mock_classify.return_value = {
            "intent": "create_event",
            "confidence": 0.9,
            "ambiguous": False
        }
        
        # Mock Level 2: Field extraction
        mock_extract.return_value = {
            "title": "Test Meeting",
            "start_time": "2025-12-20T10:00:00+05:30",
            "end_time": "2025-12-20T11:00:00+05:30",
            "description": "Test",
            "location": "Office",
            "all_day": False
        }
        
        # Mock Level 3: Validation
        mock_validate.return_value = {
            "is_valid": True,
            "missing_fields": [],
            "errors": [],
            "retry_required": False
        }
        
        result = process_user_input("Schedule a meeting tomorrow at 10am")
        
        assert result["status"] == "success"
        assert result["action"] == "create_event"
        assert result["confidence"] == 0.9
        assert "payload" in result
        assert result["payload"]["title"] == "Test Meeting"
    
    @patch('src.pipeline.pipeline.classify_intent')
    def test_low_confidence_failure(self, mock_classify):
        """Test failure when confidence is below threshold."""
        mock_classify.return_value = {
            "intent": "create_event",
            "confidence": 0.5,
            "ambiguous": True
        }
        
        result = process_user_input("Schedule something")
        
        assert result["status"] == "failure"
        assert "reason" in result
        assert "confidence" in result
    
    @patch('src.pipeline.pipeline.classify_intent')
    def test_unknown_intent(self, mock_classify):
        """Test handling of unknown intent."""
        mock_classify.return_value = {
            "intent": "unknown",
            "confidence": 0.3,
            "ambiguous": True
        }
        
        result = process_user_input("Random text")
        
        assert result["status"] == "failure"
        assert result["intent"] == "unknown"
    
    @patch('src.pipeline.pipeline.classify_intent')
    @patch('src.pipeline.pipeline.extract_fields')
    @patch('src.pipeline.pipeline.validate_fields')
    def test_validation_failure(self, mock_validate, mock_extract, mock_classify):
        """Test failure when validation fails."""
        mock_classify.return_value = {
            "intent": "create_event",
            "confidence": 0.9,
            "ambiguous": False
        }
        
        mock_extract.return_value = {
            "title": None,  # Missing required field
            "start_time": "2025-12-20T10:00:00+05:30"
        }
        
        mock_validate.return_value = {
            "is_valid": False,
            "missing_fields": ["title"],
            "errors": ["title is required"],
            "retry_required": True
        }
        
        result = process_user_input("Schedule meeting")
        
        assert result["status"] == "failure"
        assert "reason" in result


class TestConvertToPayload:
    """Test payload conversion function."""
    
    def test_convert_create_event_payload(self):
        """Test conversion for create_event."""
        extracted_fields = {
            "title": "Test Meeting",
            "start_time": "2025-12-20T10:00:00+05:30",
            "end_time": "2025-12-20T11:00:00+05:30",
            "description": "Test",
            "location": "Office",
            "all_day": False
        }
        
        payload = _convert_to_payload("create_event", extracted_fields)
        
        assert payload["title"] == "Test Meeting"
        assert payload["start_time"] == "2025-12-20T10:00:00+05:30"
        assert payload["end_time"] == "2025-12-20T11:00:00+05:30"
        assert payload["description"] == "Test"
        assert payload["location"] == "Office"
        assert payload["all_day"] is False
    
    def test_convert_update_event_payload(self):
        """Test conversion for update_event."""
        extracted_fields = {
            "event_identifier": "Test Meeting",
            "updated_fields": {
                "title": "Updated Meeting",
                "start_time": "2025-12-20T14:00:00+05:30"
            }
        }
        
        payload = _convert_to_payload("update_event", extracted_fields)
        
        assert payload["title"] == "Test Meeting"
        assert payload["start_time"] == "2025-12-20T14:00:00+05:30"
    
    def test_convert_delete_event_payload(self):
        """Test conversion for delete_event."""
        extracted_fields = {
            "event_identifier": "Test Meeting"
        }
        
        payload = _convert_to_payload("delete_event", extracted_fields)
        
        assert payload["title"] == "Test Meeting"
    
    def test_convert_list_events_payload(self):
        """Test conversion for list_events."""
        extracted_fields = {
            "start_time": "2025-12-20T00:00:00+05:30",
            "end_time": "2025-12-21T00:00:00+05:30"
        }
        
        payload = _convert_to_payload("list_events", extracted_fields)
        
        assert payload["start_time"] == "2025-12-20T00:00:00+05:30"
        assert payload["end_time"] == "2025-12-21T00:00:00+05:30"
        assert payload["title"] == ""

