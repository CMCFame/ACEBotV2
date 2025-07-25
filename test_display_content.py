# test_display_content.py
"""
Test display content extraction to debug why structured blocks are still showing
"""

import re
import json

def extract_json_object(text, start_pos):
    """Extract a complete JSON object starting from the given position."""
    if start_pos >= len(text) or text[start_pos] != '{':
        return None
    
    brace_count = 0
    in_string = False
    escape_next = False
    
    for i in range(start_pos, len(text)):
        char = text[i]
        
        if escape_next:
            escape_next = False
            continue
            
        if char == '\\' and in_string:
            escape_next = True
            continue
            
        if char == '"' and not escape_next:
            in_string = not in_string
            continue
            
        if not in_string:
            if char == '{':
                brace_count += 1
            elif char == '}':
                brace_count -= 1
                if brace_count == 0:
                    return text[start_pos:i+1]
    
    return None

def extract_display_content(raw_response):
    """Test the display content extraction function"""
    try:
        # Start with the full response
        display_content = raw_response
        
        print(f"Original response length: {len(display_content)}")
        print(f"Original content:\n{display_content[:200]}...\n")
        
        # Remove QUESTION_TRACKING blocks using robust JSON extraction
        question_tracking_match = re.search(r'QUESTION_TRACKING:\s*\{', display_content, re.DOTALL)
        if question_tracking_match:
            print("Found QUESTION_TRACKING block")
            start_pos = question_tracking_match.start()
            json_start = question_tracking_match.start() + len(question_tracking_match.group()) - 1
            json_obj = extract_json_object(display_content, json_start)
            if json_obj:
                # Remove the entire block including the label
                block_end = json_start + len(json_obj)
                print(f"Removing QUESTION_TRACKING from pos {start_pos} to {block_end}")
                display_content = display_content[:start_pos] + display_content[block_end:]
        
        # Remove COMPLETION_STATUS blocks
        completion_match = re.search(r'COMPLETION_STATUS:\s*\{', display_content, re.DOTALL)
        if completion_match:
            print("Found COMPLETION_STATUS block")
            start_pos = completion_match.start()
            json_start = completion_match.start() + len(completion_match.group()) - 1
            json_obj = extract_json_object(display_content, json_start)
            if json_obj:
                block_end = json_start + len(json_obj)
                print(f"Removing COMPLETION_STATUS from pos {start_pos} to {block_end}")
                display_content = display_content[:start_pos] + display_content[block_end:]
        
        # Clean up extra whitespace and empty lines
        display_content = re.sub(r'\n\s*\n', '\n\n', display_content)
        display_content = display_content.strip()
        
        print(f"Final display content length: {len(display_content)}")
        print(f"Final content:\n{display_content}")
        
        return display_content
        
    except Exception as e:
        print(f"Error extracting display content: {e}")
        return raw_response

def test_with_sample_response():
    """Test with the sample response you provided"""
    
    sample_response = """Thank you, Victor from ABC. It's great to have you here. Let's begin gathering information about your callout processes.

Now, let's move on to understanding more about your callout situations.

What type of situation are you typically responding to for callouts at ABC?

QUESTION_TRACKING: {"question_asked": "What type of situation are you typically responding to for callouts at ABC?", "question_id": "basic_info_callout_type_001", "topic": "basic_info", "answer_received": false, "answer_quality": "none", "follow_up_needed": false, "user_response": ""}

COMPLETION_STATUS: {"overall_progress": 10, "topic_coverage": {"basic_info": false, "staffing_details": false, "contact_process": false, "list_management": false, "insufficient_staffing": false, "calling_logistics": false, "list_changes": false, "tiebreakers": false, "additional_rules": false}, "missing_critical_info": ["callout_type", "callout_frequency", "staffing_requirements"], "current_topic_complete": false}"""
    
    print("=== Testing Display Content Extraction ===")
    result = extract_display_content(sample_response)
    
    expected_clean_content = """Thank you, Victor from ABC. It's great to have you here. Let's begin gathering information about your callout processes.

Now, let's move on to understanding more about your callout situations.

What type of situation are you typically responding to for callouts at ABC?"""
    
    print(f"\n=== Expected vs Actual ===")
    print(f"Expected: {len(expected_clean_content)} chars")
    print(f"Actual: {len(result)} chars")
    
    if "QUESTION_TRACKING" in result or "COMPLETION_STATUS" in result:
        print("[FAIL] Structured blocks still present in result")
    else:
        print("[PASS] Structured blocks successfully removed")

if __name__ == "__main__":
    test_with_sample_response()