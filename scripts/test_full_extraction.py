"""Test script to evaluate full field extraction with the actual prompt."""

import requests
import json
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pipeline.level2_extraction import extract_fields_create_event

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "llama3.2:latest"


def test_full_extraction(user_input: str) -> Dict[str, Any]:
    """
    Test full field extraction using the actual prompt.
    
    Args:
        user_input: User's text input
        
    Returns:
        Dictionary with extraction results
    """
    try:
        result = extract_fields_create_event(user_input)
        return {
            "input": user_input,
            "success": True,
            "result": result,
            "title": result.get("title"),
            "start_time": result.get("start_time"),
            "end_time": result.get("end_time"),
            "all_day": result.get("all_day"),
            "has_title": result.get("title") is not None and len(str(result.get("title", "")).strip()) > 0
        }
    except Exception as e:
        return {
            "input": user_input,
            "success": False,
            "error": str(e),
            "has_title": False
        }


def run_tests():
    """Run a series of full extraction tests."""
    
    test_cases = [
        "29th Dec meeting at CDAC with Abhishek",
        "create an event on 28th Dec 15:30 to 17:30 meeting Prathamesh Thite at Anna",
        "please create a event on 29th Dec for full day: Meeting at CDAC with Abhishek",
        "tomorrow dentist appointment",
        "team standup at 10am",
        "schedule a call with Sarah at 4 pm today",
        "create meeting with Rohan tomorrow at 11",
        "block tomorrow 3 to 5 pm for deep work",
        "add team meeting today at 3:30",
    ]
    
    print("=" * 80)
    print("FULL FIELD EXTRACTION TEST RESULTS")
    print("=" * 80)
    print()
    
    results = []
    for i, test_input in enumerate(test_cases, 1):
        print(f"Test {i}/{len(test_cases)}: {test_input}")
        result = test_full_extraction(test_input)
        results.append(result)
        
        if not result["success"]:
            print(f"  [ERROR] {result.get('error', 'Unknown error')}")
        else:
            if result["has_title"]:
                print(f"  [OK] Title: '{result['title']}'")
            else:
                print(f"  [FAILED] No title extracted!")
            
            print(f"  Start: {result.get('start_time', 'None')}")
            print(f"  End: {result.get('end_time', 'None')}")
            print(f"  All-day: {result.get('all_day', 'None')}")
        
        print()
    
    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    successful = sum(1 for r in results if r["success"])
    has_title = sum(1 for r in results if r.get("has_title"))
    total = len(results)
    
    print(f"Total tests: {total}")
    print(f"Successful extractions: {successful}/{total} ({successful/total*100:.1f}%)")
    print(f"Title extracted: {has_title}/{total} ({has_title/total*100:.1f}%)")
    print()
    
    # Show failures
    failures = [r for r in results if not r.get("has_title")]
    if failures:
        print("TITLE EXTRACTION FAILURES:")
        for r in failures:
            print(f"  - '{r['input']}'")
            if not r["success"]:
                print(f"    Error: {r.get('error')}")
            else:
                print(f"    Extracted fields: {json.dumps(r.get('result', {}), indent=2)}")
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

