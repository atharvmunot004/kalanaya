"""Unit tests for validators module."""

import pytest
from src.utils.validators import validate_intent, validate_event_params


class TestValidateIntent:
    """Test validate_intent function."""
    
    def test_valid_intent(self):
        """Test validation of valid intent."""
        intent = {
            "action": "create_event",
            "confidence": 0.9
        }
        
        is_valid, error = validate_intent(intent)
        assert is_valid is True
        assert error is None
    
    def test_missing_action(self):
        """Test validation fails when action is missing."""
        intent = {
            "confidence": 0.9
        }
        
        is_valid, error = validate_intent(intent)
        assert is_valid is False
        assert "action" in error
    
    def test_missing_confidence(self):
        """Test validation fails when confidence is missing."""
        intent = {
            "action": "create_event"
        }
        
        is_valid, error = validate_intent(intent)
        assert is_valid is False
        assert "confidence" in error
    
    def test_invalid_action(self):
        """Test validation fails with invalid action."""
        intent = {
            "action": "invalid_action",
            "confidence": 0.9
        }
        
        is_valid, error = validate_intent(intent)
        assert is_valid is False
        assert "Invalid action" in error
    
    def test_invalid_confidence_range(self):
        """Test validation fails with invalid confidence range."""
        intent = {
            "action": "create_event",
            "confidence": 1.5  # Out of range
        }
        
        is_valid, error = validate_intent(intent)
        assert is_valid is False
        assert "confidence" in error
    
    def test_valid_with_timestamps(self):
        """Test validation with valid timestamps."""
        intent = {
            "action": "create_event",
            "confidence": 0.9,
            "start_time": "2025-12-20T10:00:00+05:30",
            "end_time": "2025-12-20T11:00:00+05:30"
        }
        
        is_valid, error = validate_intent(intent)
        assert is_valid is True


class TestValidateEventParams:
    """Test validate_event_params function."""
    
    def test_valid_params(self):
        """Test validation of valid event parameters."""
        is_valid, error = validate_event_params(
            title="Test Event",
            start_time="2025-12-20T10:00:00+05:30",
            end_time="2025-12-20T11:00:00+05:30"
        )
        
        assert is_valid is True
        assert error is None
    
    def test_empty_title(self):
        """Test validation fails with empty title."""
        is_valid, error = validate_event_params(
            title="",
            start_time="2025-12-20T10:00:00+05:30"
        )
        
        assert is_valid is False
        assert "Title" in error
    
    def test_invalid_start_time_format(self):
        """Test validation fails with invalid start_time format."""
        is_valid, error = validate_event_params(
            title="Test Event",
            start_time="invalid-time"
        )
        
        assert is_valid is False
        assert "start_time" in error
    
    def test_invalid_end_time_format(self):
        """Test validation fails with invalid end_time format."""
        is_valid, error = validate_event_params(
            title="Test Event",
            start_time="2025-12-20T10:00:00+05:30",
            end_time="invalid-time"
        )
        
        assert is_valid is False
        assert "end_time" in error
    
    def test_end_time_before_start_time(self):
        """Test validation fails when end_time is before start_time."""
        is_valid, error = validate_event_params(
            title="Test Event",
            start_time="2025-12-20T11:00:00+05:30",
            end_time="2025-12-20T10:00:00+05:30"
        )
        
        assert is_valid is False
        assert "after start_time" in error
    
    def test_valid_without_end_time(self):
        """Test validation passes without end_time."""
        is_valid, error = validate_event_params(
            title="Test Event",
            start_time="2025-12-20T10:00:00+05:30",
            end_time=None
        )
        
        assert is_valid is True

