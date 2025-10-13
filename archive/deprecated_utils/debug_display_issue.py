# debug_display_issue.py
"""
Debug why structured blocks are still showing in the UI
"""

def simulate_ai_service_flow():
    """Simulate the AI service flow to find where the issue occurs"""
    
    # This is what the AI returns (raw response)
    raw_ai_response = """Thank you, Victor from ABC. It's great to have you here. Let's begin gathering information about your callout processes.

Now, let's move on to understanding more about your callout situations.

What type of situation are you typically responding to for callouts at ABC?

QUESTION_TRACKING: {"question_asked": "What type of situation are you typically responding to for callouts at ABC?", "question_id": "basic_info_callout_type_001", "topic": "basic_info", "answer_received": false, "answer_quality": "none", "follow_up_needed": false, "user_response": ""}

COMPLETION_STATUS: {"overall_progress": 10, "topic_coverage": {"basic_info": false, "staffing_details": false, "contact_process": false, "list_management": false, "insufficient_staffing": false, "calling_logistics": false, "list_changes": false, "tiebreakers": false, "additional_rules": false}, "missing_critical_info": ["callout_type", "callout_frequency", "staffing_requirements"], "current_topic_complete": false}"""

    print("=== Debugging AI Service Flow ===")
    print(f"1. Raw AI Response Length: {len(raw_ai_response)}")
    
    # Step 1: Parse structured response (should work)
    # Step 2: Extract display content (should work - we tested this)
    
    # Simulate the extraction like the AI service does
    import re
    
    def extract_json_object(text, start_pos):
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
    
    def extract_display_content_simulation(raw_response):
        try:
            display_content = raw_response
            
            # Remove QUESTION_TRACKING blocks
            question_tracking_match = re.search(r'QUESTION_TRACKING:\s*\{', display_content, re.DOTALL)
            if question_tracking_match:
                start_pos = question_tracking_match.start()
                json_start = question_tracking_match.start() + len(question_tracking_match.group()) - 1
                json_obj = extract_json_object(display_content, json_start)
                if json_obj:
                    block_end = json_start + len(json_obj)
                    display_content = display_content[:start_pos] + display_content[block_end:]
            
            # Remove COMPLETION_STATUS blocks
            completion_match = re.search(r'COMPLETION_STATUS:\s*\{', display_content, re.DOTALL)
            if completion_match:
                start_pos = completion_match.start()
                json_start = completion_match.start() + len(completion_match.group()) - 1
                json_obj = extract_json_object(display_content, json_start)
                if json_obj:
                    block_end = json_start + len(json_obj)
                    display_content = display_content[:start_pos] + display_content[block_end:]
            
            # Clean up extra whitespace
            display_content = re.sub(r'\n\s*\n', '\n\n', display_content)
            display_content = display_content.strip()
            
            return display_content
            
        except Exception as e:
            print(f"Error: {e}")
            return raw_response
    
    # Test extraction
    display_content = extract_display_content_simulation(raw_ai_response)
    
    print(f"2. Display Content Length: {len(display_content)}")
    print(f"3. Contains QUESTION_TRACKING: {'QUESTION_TRACKING' in display_content}")
    print(f"4. Contains COMPLETION_STATUS: {'COMPLETION_STATUS' in display_content}")
    
    print(f"\n=== Display Content ===")
    print(display_content)
    
    if "QUESTION_TRACKING" in display_content or "COMPLETION_STATUS" in display_content:
        print("\n❌ PROBLEM: Structured blocks still present after extraction")
        print("This suggests the issue is in the AI service implementation")
    else:
        print("\n✅ SUCCESS: Display content is clean")
        print("The issue might be elsewhere in the app flow")
    
    # Check what should be stored in session state
    print(f"\n=== What Should Happen ===")
    print(f"- chat_history should get: display_content (clean)")
    print(f"- visible_messages should get: display_content (clean)")
    print(f"- User should see: clean conversation without JSON blocks")

if __name__ == "__main__":
    simulate_ai_service_flow()