"""Main entry point for Kalanaya voice-controlled calendar assistant."""

import sys
import json
import os
from pathlib import Path
from typing import Optional, Dict, Any, List

# Set UTF-8 encoding for Windows console
if sys.platform == 'win32':
    try:
        # Try to set UTF-8 encoding for stdout/stderr
        if hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8')
        if hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8')
        # Also set environment variable
        os.environ['PYTHONIOENCODING'] = 'utf-8'
    except Exception:
        pass  # If it fails, continue anyway

from src.pipeline.pipeline import process_user_input
from src.router import route
from src.speech import record_audio, record_audio_until_stop, transcribe
from src.utils.logging import setup_logger

# Calculate logs directory
# Use current working directory when installed, or project root when run directly
_current_file = Path(__file__).resolve()
if 'site-packages' in str(_current_file) or 'dist-packages' in str(_current_file):
    # Installed as package - use current working directory
    import os
    _logs_dir = Path(os.getcwd()) / "logs"
else:
    # Running directly - go up from src/main.py
    _PROJECT_ROOT = _current_file.parent.parent
    _logs_dir = _PROJECT_ROOT / "logs"

# Set up logger
_logs_dir.mkdir(exist_ok=True)
logger = setup_logger("main", log_file=_logs_dir / "main.log")


# Note: The multi-level pipeline handles intent locking internally.
# No need for InteractionState anymore as the pipeline architecture
# enforces no reclassification after intent lock.


def process_text_command(text: str) -> dict:
    """
    Process a text command through the multi-level pipeline.
    
    Args:
        text: User's text command
        
    Returns:
        Dictionary with action result
    """
    logger.info(f"Processing text command: {text}")
    
    try:
        # Process through multi-level pipeline
        pipeline_result = process_user_input(text)
        
        # Route to calendar actions
        result = route(pipeline_result)
        logger.info(f"Action result: status={result.get('status')}, action={result.get('action')}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error processing text command: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "action": "none",
            "error": f"Failed to process command: {str(e)}",
            "confidence": 0.0,
        }


def process_voice_command() -> dict:
    """
    Process a voice command through the full pipeline.
    Uses press-to-start/stop recording.
    
    Returns:
        Dictionary with action result
    """
    logger.info("Processing voice command (press-to-start/stop)")
    
    try:
        # Step 1: Record audio (press Enter to start, Enter to stop)
        logger.debug("Recording audio")
        audio_file = record_audio_until_stop()
        logger.debug(f"Audio recorded to: {audio_file}")
        
        # Step 2: Transcribe audio to text
        logger.debug("Transcribing audio to text")
        print("🔄 Transcribing...")
        text = transcribe(audio_file)
        logger.info(f"Transcribed text: {text}")
        print(f"📝 Transcribed: {text}")
        
        # Clean up audio file
        try:
            Path(audio_file).unlink()
            logger.debug("Audio file cleaned up")
        except Exception as e:
            logger.warning(f"Failed to delete audio file: {e}")
        
        # Step 3: Process text command
        return process_text_command(text)
        
    except Exception as e:
        logger.error(f"Error processing voice command: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "action": "none",
            "error": f"Failed to process voice command: {str(e)}",
            "confidence": 0.0,
        }


def format_result(result: dict, is_clarification: bool = False) -> str:
    """
    Format action result for user-friendly display.
    
    Args:
        result: Action result dictionary
        
    Returns:
        Formatted string
    """
    status = result.get("status", "unknown")
    action = result.get("action", "unknown")
    
    if status == "success":
        if action == "create_event":
            event_id = result.get("event_id", "N/A")
            summary = result.get("summary", "N/A")
            html_link = result.get("html_link", "")
            return f"✅ Event created successfully!\n   Title: {summary}\n   ID: {event_id}\n   Link: {html_link}"
        
        elif action == "update_event":
            event_id = result.get("event_id", "N/A")
            summary = result.get("summary", "N/A")
            return f"✅ Event updated successfully!\n   Title: {summary}\n   ID: {event_id}"
        
        elif action == "delete_event":
            event_id = result.get("event_id", "N/A")
            return f"✅ Event deleted successfully!\n   ID: {event_id}"
        
        elif action == "list_events":
            events = result.get("events", [])
            count = result.get("count", 0)
            if count == 0:
                return "📅 No events found in the specified time range."
            
            output = f"📅 Found {count} event(s):\n"
            for i, event in enumerate(events, 1):
                summary = event.get("summary", "Untitled")
                start = event.get("start", {})
                start_time = start.get("dateTime") or start.get("date", "Unknown")
                output += f"   {i}. {summary} - {start_time}\n"
            return output
        
        elif action == "none":
            message = result.get("message", "No action to perform")
            return f"ℹ️  {message}"
        
        else:
            return f"✅ Action '{action}' completed successfully"
    
    else:
        error = result.get("error", "Unknown error")
        return f"❌ Error: {error}"


def text_mode():
    """Run in text input mode."""
    print("\n🎙️  Kalanaya - Voice Calendar Assistant (Text Mode)")
    print("=" * 60)
    print("Type your calendar command. Commands:")
    print("  - 'voice' or 'v' to switch to voice mode")
    print("  - 'exit' or 'quit' to quit")
    print("=" * 60)
    print()
    
    while True:
        try:
            user_input = input("🗣️  You: ").strip()
            
            if user_input.lower() in {"exit", "quit", "q"}:
                print("👋 Exiting Kalanaya. Goodbye!")
                break
            
            if user_input.lower() in {"voice", "v"}:
                print("\n🎤 Switching to voice mode...")
                voice_mode()
                continue
            
            if not user_input:
                continue
            
            # Process command
            result = process_text_command(user_input)
            
            # Display result
            print("\n🤖 Kalanaya:")
            print(format_result(result))
            print()
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted. Exiting.")
            break
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            print(f"\n❌ Unexpected error: {str(e)}")
            print()


def voice_mode():
    """Run in voice input mode."""
    print("\n🎤  Kalanaya - Voice Calendar Assistant (Voice Mode)")
    print("=" * 60)
    print("Voice commands:")
    print("  - Press Enter to start recording")
    print("  - Press Enter again to stop recording")
    print("  - Type 'text' or 't' to switch to text mode")
    print("  - Type 'exit' or 'quit' to quit")
    print("=" * 60)
    print()
    
    while True:
        try:
            user_input = input("Press Enter to start recording, or type command: ").strip()
            
            if user_input.lower() in {"exit", "quit", "q"}:
                print("👋 Exiting Kalanaya. Goodbye!")
                break
            
            if user_input.lower() in {"text", "t"}:
                print("\n⌨️  Switching to text mode...")
                text_mode()
                return
            
            # If user just pressed Enter (empty input), start recording
            if not user_input:
                # Process voice command
                result = process_voice_command()
                
                # Display result
                print("\n🤖 Kalanaya:")
                print(format_result(result))
                print()
            else:
                print("⚠️  Invalid command. Press Enter to record or type 'text'/'exit'.")
            
        except KeyboardInterrupt:
            print("\n👋 Interrupted. Exiting.")
            break
        
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            print(f"\n❌ Unexpected error: {str(e)}")
            print()


def main():
    """Main entry point."""
    logger.info("Starting Kalanaya application")
    
    try:
        # Initialize pipeline
        print("🔄 Initializing multi-level pipeline...")
        logger.info("Multi-level pipeline initialized")
        print("✅ Ready!\n")
        
        # Start in text mode by default
        text_mode()
        
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}", exc_info=True)
        print(f"\n❌ Failed to start application: {str(e)}")
        print("Please check your configuration and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
