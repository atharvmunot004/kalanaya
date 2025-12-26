"""Test script to evaluate llama3.2's title extraction capabilities."""

import requests
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

# Try to use zoneinfo (Python 3.9+), fallback to UTC offset for Windows compatibility
try:
    from zoneinfo import ZoneInfo
    TZ = ZoneInfo("Asia/Kolkata")
except (ImportError, ModuleNotFoundError, LookupError):
    # Fallback: Asia/Kolkata is UTC+5:30
    TZ = timezone(timedelta(hours=5, minutes=30))

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"


def _get_temporal_anchors() -> Dict[str, str]:
    """Get current date/time information."""
    now = datetime.now(TZ)
    tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")
    day_after_tomorrow = (now + timedelta(days=2)).strftime("%Y-%m-%d")
    return {
        "current_date": now.strftime("%Y-%m-%d"),
        "current_time": now.strftime("%H:%M:%S"),
        "current_datetime_iso": now.isoformat(),
        "current_day_name": now.strftime("%A"),
        "current_date_readable": now.strftime("%B %d, %Y"),
        "current_year": str(now.year),
        "tomorrow": tomorrow,
        "day_after_tomorrow": day_after_tomorrow,
    }


def _call_ollama(prompt: str) -> str:
    """Call Ollama API with the given prompt."""
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": MODEL,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0
            }
        },
        timeout=60,
    )
    
    response.raise_for_status()
    response_data = response.json()
    
    if "error" in response_data:
        raise Exception(f"Ollama API error: {response_data['error']}")
    
    if "response" in response_data:
        return response_data["response"].strip()
    elif "content" in response_data:
        return response_data["content"].strip()
    elif isinstance(response_data, str):
        return response_data.strip()
    else:
        raise KeyError(f"'response' key not found in Ollama API response. Available keys: {list(response_data.keys())}")


def test_title_extraction(user_input: str, expected_title: str = None) -> Dict[str, Any]:
    """
    Test title extraction with a simple, focused prompt.
    
    Args:
        user_input: User's text input
        expected_title: Expected title (for comparison)
        
    Returns:
        Dictionary with test results
    """
    anchors = _get_temporal_anchors()
    
    # Simple, focused prompt for title extraction only
    prompt = f"""Extract the event title from this calendar command. Return ONLY the title as a JSON string.

RULES:
- Title should be 2-5 words
- Remove dates, times, and filler words (create, event, on, at, for, etc.)
- Keep the core event name/subject
- Output format: {{"title": "extracted title"}}

Examples:
- "29th Dec meeting at CDAC with Abhishek" → {{"title": "CDAC Meeting with Abhishek"}}
- "create an event on 28th Dec 15:30 to 17:30 meeting Prathamesh Thite at Anna" → {{"title": "Meeting Prathamesh Thite at Anna"}}
- "tomorrow dentist appointment" → {{"title": "Dentist Appointment"}}
- "team standup at 10am" → {{"title": "Team Standup"}}

User input: {user_input}

Output (JSON only):"""
    
    try:
        response_text = _call_ollama(prompt)
        
        # Parse JSON response
        response_text = response_text.strip()
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            json_lines = []
            in_json = False
            for line in lines:
                if line.strip().startswith("```"):
                    in_json = not in_json
                    continue
                if in_json:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)
        
        # Try to extract JSON if embedded
        if "{" in response_text and "}" in response_text:
            start_idx = response_text.find("{")
            end_idx = response_text.rfind("}") + 1
            if start_idx >= 0 and end_idx > start_idx:
                response_text = response_text[start_idx:end_idx]
        
        result = json.loads(response_text)
        extracted_title = result.get("title", None)
        
        return {
            "input": user_input,
            "extracted_title": extracted_title,
            "expected_title": expected_title,
            "match": extracted_title == expected_title if expected_title else None,
            "success": extracted_title is not None and len(extracted_title.strip()) > 0
        }
        
    except Exception as e:
        return {
            "input": user_input,
            "extracted_title": None,
            "expected_title": expected_title,
            "error": str(e),
            "success": False
        }


def run_tests():
    """Run a series of title extraction tests."""
    
    test_cases = [
        {
            "input": "29th Dec meeting at CDAC with Abhishek",
            "expected": "CDAC Meeting with Abhishek"
        },
        {
            "input": "create an event on 28th Dec 15:30 to 17:30 meeting Prathamesh Thite at Anna",
            "expected": "Meeting Prathamesh Thite at Anna"
        },
        {
            "input": "please create a event on 29th Dec for full day: Meeting at CDAC with Abhishek",
            "expected": "Meeting at CDAC with Abhishek"
        },
        {
            "input": "tomorrow dentist appointment",
            "expected": "Dentist Appointment"
        },
        {
            "input": "team standup at 10am",
            "expected": "Team Standup"
        },
        {
            "input": "schedule a call with Sarah at 4 pm today",
            "expected": "Call with Sarah"
        },
        {
            "input": "create meeting with Rohan tomorrow at 11",
            "expected": "Meeting with Rohan"
        },
        {
            "input": "block tomorrow 3 to 5 pm for deep work",
            "expected": "Deep Work"
        },
        {
            "input": "add team meeting today at 3:30",
            "expected": "Team Meeting"
        },
        {
            "input": "29th Dec meeting at CDAC with Abhishek",
            "expected": "CDAC Meeting with Abhishek"
        },
    ]
    
    print("=" * 80)
    print("TITLE EXTRACTION TEST RESULTS")
    print("=" * 80)
    print()
    
    results = []
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_case['input']}")
        result = test_title_extraction(test_case['input'], test_case['expected'])
        results.append(result)
        
        if result.get("error"):
            print(f"  [ERROR] {result['error']}")
        elif result["success"]:
            print(f"  [OK] Extracted: '{result['extracted_title']}'")
            if result.get('expected_title'):
                if result.get('match'):
                    print(f"  [MATCH] Expected: '{result['expected_title']}'")
                else:
                    print(f"  [MISMATCH] Expected: '{result['expected_title']}'")
        else:
            print(f"  [FAILED] No title extracted")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    successful = sum(1 for r in results if r["success"])
    matched = sum(1 for r in results if r.get("match") is True)
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Successful extractions: {successful}/{total} ({successful/total*100:.1f}%)")
    if any(r.get("expected") for r in results):
        print(f"Matches expected: {matched}/{total} ({matched/total*100:.1f}%)")
    print()
    
    # Show failures
    failures = [r for r in results if not r["success"]]
    if failures:
        print("FAILED EXTRACTIONS:")
        for r in failures:
            print(f"  - '{r['input']}'")
            if r.get("error"):
                print(f"    Error: {r['error']}")
        print()
    
    # Show mismatches
    mismatches = [r for r in results if r.get("match") is False]
    if mismatches:
        print("MISMATCHES:")
        for r in mismatches:
            print(f"  - Input: '{r['input']}'")
            print(f"    Extracted: '{r['extracted_title']}'")
            if r.get('expected_title'):
                print(f"    Expected: '{r['expected_title']}'")
        print()
    
    return results


if __name__ == "__main__":
    try:
        results = run_tests()
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        import traceback
        traceback.print_exc()

