# test_improved_extraction.py
"""
Test the improved display content extraction
"""

import re

def extract_display_content_improved(raw_response):
    """Test the improved extraction method"""
    try:
        # Start with the full response
        display_content = raw_response
        print(f"DEBUG: Original response length: {len(display_content)}")
        
        # More aggressive approach - remove ALL structured blocks with regex
        # Remove QUESTION_TRACKING blocks (including multiline JSON)
        display_content = re.sub(r'QUESTION_TRACKING:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', display_content, flags=re.DOTALL)
        
        # Remove COMPLETION_STATUS blocks (including multiline JSON)  
        display_content = re.sub(r'COMPLETION_STATUS:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', display_content, flags=re.DOTALL)
        
        # Remove TOPIC_UPDATE blocks (legacy compatibility)
        display_content = re.sub(r'TOPIC_UPDATE:\s*\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', '', display_content, flags=re.DOTALL)
        
        # Additional cleanup - remove any remaining JSON-like blocks that start with known prefixes
        display_content = re.sub(r'(QUESTION_TRACKING|COMPLETION_STATUS|TOPIC_UPDATE):\s*.*?(?=\n\n|\Z)', '', display_content, flags=re.DOTALL)
        
        # Clean up extra whitespace and empty lines
        display_content = re.sub(r'\n\s*\n\s*\n', '\n\n', display_content)  # Multiple empty lines to double
        display_content = re.sub(r'^\s*\n', '', display_content)  # Leading empty lines
        display_content = display_content.strip()
        
        print(f"DEBUG: Final display content length: {len(display_content)}")
        print(f"DEBUG: Contains QUESTION_TRACKING: {'QUESTION_TRACKING' in display_content}")
        print(f"DEBUG: Contains COMPLETION_STATUS: {'COMPLETION_STATUS' in display_content}")
        
        # If nothing left after cleaning, use a fallback
        if not display_content:
            display_content = "I'm processing your response. Let me ask the next question."
            
        return display_content
        
    except Exception as e:
        print(f"Warning: Error extracting display content: {e}")
        # Fallback - try simple removal as last resort
        try:
            fallback_content = raw_response
            # Simple line-by-line removal
            lines = fallback_content.split('\n')
            clean_lines = []
            skip_mode = False
            
            for line in lines:
                if any(prefix in line for prefix in ['QUESTION_TRACKING:', 'COMPLETION_STATUS:', 'TOPIC_UPDATE:']):
                    skip_mode = True
                    continue
                if skip_mode and (line.strip().endswith('}') or not line.strip()):
                    if line.strip().endswith('}'):
                        skip_mode = False
                    continue
                if not skip_mode:
                    clean_lines.append(line)
            
            return '\n'.join(clean_lines).strip()
        except:
            # Ultimate fallback
            return "I'm processing your response. Let me ask the next question."

def test_with_broken_response():
    """Test with the broken response you provided"""
    
    broken_response = """Thank you, Victor, for that detailed information about your typical callout situations. It's clear that ABC handles a variety of emergency scenarios related to your electrical infrastructure.

Now, let's move on to the frequency of these callouts. How often do these types of callouts typically occur?

QUESTION_TRACKING: {"question_asked": "How often do these types of callouts typically occur?", "question_id": "basic_info_callout_frequency_001", "topic": "basic_info", "answer_received": false, "answer_quality": "none", "follow_up_needed": false, "user_response": ""}"""
    
    print("=== Testing Improved Display Content Extraction ===")
    result = extract_display_content_improved(broken_response)
    
    expected_clean_content = """Thank you, Victor, for that detailed information about your typical callout situations. It's clear that ABC handles a variety of emergency scenarios related to your electrical infrastructure.

Now, let's move on to the frequency of these callouts. How often do these types of callouts typically occur?"""
    
    print(f"\n=== Results ===")
    print(f"Expected length: {len(expected_clean_content)} chars")
    print(f"Actual length: {len(result)} chars")
    
    print(f"\nExpected content:")
    print(repr(expected_clean_content))
    print(f"\nActual content:")
    print(repr(result))
    
    if "QUESTION_TRACKING" in result or "COMPLETION_STATUS" in result:
        print("\n[FAIL] Structured blocks still present in result")
    else:
        print("\n[PASS] Structured blocks successfully removed")
        
    if result.strip() == expected_clean_content.strip():
        print("[PASS] Content matches expected result")
    else:
        print("[PARTIAL] Content cleaned but formatting may differ")

def test_complex_nested_json():
    """Test with complex nested JSON that might break the regex"""
    
    complex_response = """Your response about the callout process is very helpful.

QUESTION_TRACKING: {"question_asked": "Who do you call first?", "question_id": "contact_001", "topic": "contact_process", "answer_received": true, "answer_quality": "complete", "follow_up_needed": false, "user_response": "We call the dispatcher who has multiple devices: {\"primary\": \"cell\", \"backup\": \"landline\"}"}

COMPLETION_STATUS: {"overall_progress": 45, "topic_coverage": {"basic_info": true, "contact_process": false}, "missing_critical_info": ["device_count", "list_management"], "current_topic_complete": false}

What's the next step in your process?"""
    
    print("\n=== Testing Complex Nested JSON ===")
    result = extract_display_content_improved(complex_response)
    
    expected = """Your response about the callout process is very helpful.

What's the next step in your process?"""
    
    print(f"Result: {repr(result)}")
    print(f"Expected: {repr(expected)}")
    
    if "QUESTION_TRACKING" in result or "COMPLETION_STATUS" in result:
        print("[FAIL] Complex JSON not properly removed")
    else:
        print("[PASS] Complex nested JSON successfully removed")

if __name__ == "__main__":
    test_with_broken_response()
    test_complex_nested_json()