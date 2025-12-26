"""End-to-end tests for the full pipeline."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from src.main import process_text_command
from src.pipeline.pipeline import process_user_input


class TestEndToEndPipeline:
    """Test the complete end-to-end pipeline flow."""
    
    @patch('src.pipeline.level1_intent._call_ollama')
    @patch('src.pipeline.level2_extraction._call_ollama')
    @patch('src.router.router.get_calendar_service')
    @patch('src.router.router.create_event')
    def test_e2e_create_event_success(self, mock_create, mock_get_service, 
                                       mock_extract_ollama, mock_intent_ollama, 
                                       mock_calendar_service):
        """Test end-to-end create_event flow."""
        # Mock Level 1: Intent classification
        mock_intent_ollama.return_value = '{"intent": "create_event", "confidence": 0.9, "ambiguous": false}'
        
        # Mock Level 2: Field extraction (semantic and time)
        semantic_response = '{"title": "Team Meeting", "description": "Weekly sync", "location": "Office"}'
        time_response = '{"start_time": "2025-12-20T10:00:00+05:30", "end_time": "2025-12-20T11:00:00+05:30", "all_day": false}'
        mock_extract_ollama.side_effect = [semantic_response, time_response]
        
        # Mock calendar service
        mock_get_service.return_value = mock_calendar_service
        
        # Mock create_event
        mock_create.return_value = {
            "status": "success",
            "action": "create_event",
            "event_id": "test123",
            "html_link": "https://calendar.google.com/event?eid=test123"
        }
        
        result = process_user_input("Schedule a team meeting tomorrow at 10am")
        
        assert result["status"] == "success"
        assert result["action"] == "create_event"
        assert result["payload"]["title"] == "Team Meeting"
        assert result["payload"]["start_time"] == "2025-12-20T10:00:00+05:30"
    
    @patch('src.pipeline.level1_intent._call_ollama')
    @patch('src.router.router.get_calendar_service')
    @patch('src.router.router.list_events')
    def test_e2e_list_events_success(self, mock_list, mock_get_service, 
                                      mock_intent_ollama, mock_calendar_service):
        """Test end-to-end list_events flow."""
        # Mock Level 1: Intent classification
        mock_intent_ollama.return_value = '{"intent": "list_events", "confidence": 0.95, "ambiguous": false}'
        
        # Mock Level 2: Field extraction
        with patch('src.pipeline.level2_extraction._call_ollama') as mock_extract:
            mock_extract.return_value = '{"start_time": "2025-12-20T00:00:00+05:30", "end_time": "2025-12-21T00:00:00+05:30"}'
            
            # Mock calendar service
            mock_get_service.return_value = mock_calendar_service
            
            # Mock list_events
            mock_list.return_value = {
                "status": "success",
                "action": "list_events",
                "events": [
                    {
                        "id": "event1",
                        "summary": "Meeting 1",
                        "start": {"dateTime": "2025-12-20T10:00:00+05:30"},
                        "end": {"dateTime": "2025-12-20T11:00:00+05:30"}
                    }
                ],
                "count": 1
            }
            
            result = process_user_input("What do I have today?")
            
            assert result["status"] == "success"
            assert result["action"] == "list_events"
    
    @patch('src.pipeline.level1_intent._call_ollama')
    def test_e2e_low_confidence_failure(self, mock_intent_ollama):
        """Test end-to-end flow with low confidence."""
        mock_intent_ollama.return_value = '{"intent": "create_event", "confidence": 0.5, "ambiguous": true}'
        
        result = process_user_input("Schedule something")
        
        assert result["status"] == "failure"
        assert "confidence" in result["reason"] or "ambiguous" in result["reason"]
    
    @patch('src.pipeline.level1_intent._call_ollama')
    @patch('src.pipeline.level2_extraction._call_ollama')
    def test_e2e_validation_failure(self, mock_extract_ollama, mock_intent_ollama):
        """Test end-to-end flow with validation failure."""
        # Mock Level 1: Intent classification
        mock_intent_ollama.return_value = '{"intent": "create_event", "confidence": 0.9, "ambiguous": false}'
        
        # Mock Level 2: Field extraction with missing title
        semantic_response = '{"title": null, "description": null, "location": null}'
        time_response = '{"start_time": "2025-12-20T10:00:00+05:30", "end_time": null, "all_day": false}'
        mock_extract_ollama.side_effect = [semantic_response, time_response]
        
        result = process_user_input("Schedule meeting")
        
        assert result["status"] == "failure"
        assert "title" in result["reason"] or "Missing" in result["reason"]


class TestEndToEndMain:
    """Test end-to-end through main module."""
    
    @patch('src.main.process_user_input')
    @patch('src.main.route')
    def test_process_text_command_success(self, mock_route, mock_process):
        """Test process_text_command with successful pipeline."""
        mock_process.return_value = {
            "status": "success",
            "action": "create_event",
            "payload": {
                "title": "Test Meeting",
                "start_time": "2025-12-20T10:00:00+05:30"
            },
            "confidence": 0.9
        }
        
        mock_route.return_value = {
            "status": "success",
            "action": "create_event",
            "event_id": "test123"
        }
        
        result = process_text_command("Schedule a meeting tomorrow at 10am")
        
        assert result["status"] == "success"
        assert result["action"] == "create_event"
    
    @patch('src.main.process_user_input')
    def test_process_text_command_pipeline_failure(self, mock_process):
        """Test process_text_command with pipeline failure."""
        mock_process.return_value = {
            "status": "failure",
            "reason": "Low confidence",
            "intent": "create_event",
            "confidence": 0.5
        }
        
        result = process_text_command("Schedule something")
        
        assert result["status"] == "error"
        assert "error" in result

