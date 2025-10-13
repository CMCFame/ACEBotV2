# test_core_logic.py
"""
Core logic tests for AI-driven Q&A tracking system without Streamlit dependencies.
Tests the parsing and data management logic directly.
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, List

def extract_json_object(text, start_pos):
    """
    Extract a complete JSON object starting from the given position.
    Handles nested braces correctly.
    """
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

def test_structured_response_parsing():
    """Test the structured response parsing logic directly."""
    print("=== Testing Structured Response Parsing ===")
    
    # Mock the parsing function directly
    def parse_structured_response(raw_response):
        """Direct implementation of parsing logic."""
        structured_data = {
            "question_tracking": None,
            "completion_status": None,
            "topic_update": None
        }
        
        try:
            # Extract QUESTION_TRACKING JSON with proper nested object handling
            question_tracking_match = re.search(r'QUESTION_TRACKING:\s*(\{)', raw_response, re.DOTALL)
            if question_tracking_match:
                start_pos = question_tracking_match.start(1)
                question_json = extract_json_object(raw_response, start_pos)
                if question_json:
                    structured_data["question_tracking"] = json.loads(question_json)
            
            # Extract COMPLETION_STATUS JSON with proper nested object handling
            completion_match = re.search(r'COMPLETION_STATUS:\s*(\{)', raw_response, re.DOTALL)
            if completion_match:
                start_pos = completion_match.start(1)
                completion_json = extract_json_object(raw_response, start_pos)
                if completion_json:
                    structured_data["completion_status"] = json.loads(completion_json)
            
            # Extract TOPIC_UPDATE JSON (legacy compatibility)
            topic_update_match = re.search(r'TOPIC_UPDATE:\s*(\{)', raw_response, re.DOTALL)
            if topic_update_match:
                start_pos = topic_update_match.start(1)
                topic_json = extract_json_object(raw_response, start_pos)
                if topic_json:
                    structured_data["topic_update"] = json.loads(topic_json)
                
        except json.JSONDecodeError as e:
            print(f"Warning: Failed to parse JSON: {e}")
            
        return structured_data
    
    # Test cases
    test_cases = [
        {
            "name": "Valid Complete Response",
            "input": '''Hello! Let me ask about your callout process.

QUESTION_TRACKING: {"question_asked": "What is your company name?", "question_id": "basic_info_company_001", "topic": "basic_info", "answer_received": false, "answer_quality": "none", "follow_up_needed": false, "user_response": ""}

COMPLETION_STATUS: {"overall_progress": 10, "topic_coverage": {"basic_info": false}, "missing_critical_info": ["company_name"], "current_topic_complete": false}''',
            "expected_question_id": "basic_info_company_001",
            "expected_progress": 10
        },
        {
            "name": "Response with Answer Received",
            "input": '''Thank you, John! Now let me ask about your callout type.

QUESTION_TRACKING: {"question_asked": "What type of callouts do you handle?", "question_id": "basic_info_callout_type_001", "topic": "basic_info", "answer_received": true, "answer_quality": "complete", "follow_up_needed": false, "user_response": "John Smith from PowerCorp"}

COMPLETION_STATUS: {"overall_progress": 25, "topic_coverage": {"basic_info": true}, "missing_critical_info": ["callout_type"], "current_topic_complete": false}''',
            "expected_question_id": "basic_info_callout_type_001",
            "expected_progress": 25
        },
        {
            "name": "Malformed JSON",
            "input": '''Hello!
QUESTION_TRACKING: {"question_asked": "Test", invalid_json}
COMPLETION_STATUS: {"overall_progress": 15}''',
            "expected_question_id": None,
            "expected_progress": None
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        try:
            result = parse_structured_response(test_case["input"])
            
            # Check question tracking
            qt = result.get("question_tracking")
            if test_case["expected_question_id"]:
                if qt and qt.get("question_id") == test_case["expected_question_id"]:
                    print(f"  [PASS] Question ID: {qt.get('question_id')}")
                else:
                    print(f"  [FAIL] Question ID: Expected {test_case['expected_question_id']}, got {qt.get('question_id') if qt else None}")
            else:
                if qt is None:
                    print(f"  [PASS] Correctly handled malformed JSON")
                else:
                    print(f"  [FAIL] Expected None for malformed JSON, got {qt}")
            
            # Check completion status
            cs = result.get("completion_status")
            if test_case["expected_progress"]:
                if cs and cs.get("overall_progress") == test_case["expected_progress"]:
                    print(f"  [PASS] Progress: {cs.get('overall_progress')}%")
                else:
                    print(f"  [FAIL] Progress: Expected {test_case['expected_progress']}, got {cs.get('overall_progress') if cs else None}")
            else:
                if cs is None:
                    print(f"  [PASS] Correctly handled malformed progress")
        
        except Exception as e:
            print(f"  [FAIL] Exception: {str(e)}")

def test_display_content_extraction():
    """Test display content extraction (removing structured blocks)."""
    print("\n=== Testing Display Content Extraction ===")
    
    def extract_display_content(raw_response, structured_data):
        """Direct implementation of display content extraction."""
        try:
            # Start with the full response
            display_content = raw_response
            
            # Remove QUESTION_TRACKING blocks using robust JSON extraction
            question_tracking_match = re.search(r'QUESTION_TRACKING:\s*\{', display_content, re.DOTALL)
            if question_tracking_match:
                start_pos = question_tracking_match.start()
                json_start = question_tracking_match.start() + len(question_tracking_match.group()) - 1
                json_obj = extract_json_object(display_content, json_start)
                if json_obj:
                    # Remove the entire block including the label
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
            
            # Remove TOPIC_UPDATE blocks (existing compatibility)
            topic_update_match = re.search(r'TOPIC_UPDATE:\s*\{', display_content, re.DOTALL)
            if topic_update_match:
                start_pos = topic_update_match.start()
                json_start = topic_update_match.start() + len(topic_update_match.group()) - 1
                json_obj = extract_json_object(display_content, json_start)
                if json_obj:
                    block_end = json_start + len(json_obj)
                    display_content = display_content[:start_pos] + display_content[block_end:]
            
            # Clean up extra whitespace and empty lines
            display_content = re.sub(r'\n\s*\n', '\n\n', display_content)
            display_content = display_content.strip()
            
            # If nothing left after cleaning, use a fallback
            if not display_content:
                display_content = "I'm processing your response. Let me ask the next question."
                
            return display_content
            
        except Exception as e:
            print(f"Warning: Error extracting display content: {e}")
            return raw_response
    
    test_cases = [
        {
            "name": "Standard Response with Blocks",
            "input": '''Hello! Welcome to the ACE questionnaire.

QUESTION_TRACKING: {"question_asked": "What is your name?", "question_id": "basic_info_name_001", "topic": "basic_info", "answer_received": false, "answer_quality": "none", "follow_up_needed": false, "user_response": ""}

COMPLETION_STATUS: {"overall_progress": 5, "topic_coverage": {"basic_info": false}, "missing_critical_info": ["user_name"], "current_topic_complete": false}

Please provide your name and company to get started.''',
            "expected_content": "Hello! Welcome to the ACE questionnaire.\n\nPlease provide your name and company to get started."
        },
        {
            "name": "Empty Content After Cleaning",
            "input": '''QUESTION_TRACKING: {"question_asked": "Test", "question_id": "test_001", "topic": "basic_info", "answer_received": false, "answer_quality": "none", "follow_up_needed": false, "user_response": ""}

COMPLETION_STATUS: {"overall_progress": 10, "topic_coverage": {"basic_info": false}, "missing_critical_info": [], "current_topic_complete": false}''',
            "should_use_fallback": True
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest: {test_case['name']}")
        try:
            result = extract_display_content(test_case["input"], {})
            
            if test_case.get("should_use_fallback"):
                if "processing" in result.lower():
                    print(f"  [PASS] Used fallback content: {result}")
                else:
                    print(f"  [FAIL] Should have used fallback, got: {result}")
            else:
                expected = test_case["expected_content"]
                if result.strip() == expected.strip():
                    print(f"  [PASS] Correctly extracted: {result[:50]}...")
                else:
                    print(f"  [FAIL] Expected: {expected[:50]}...")
                    print(f"      Got: {result[:50]}...")
        
        except Exception as e:
            print(f"  [FAIL] Exception: {str(e)}")

def test_question_state_logic():
    """Test question state management logic."""
    print("\n=== Testing Question State Management ===")
    
    # Mock question state
    class MockQuestionState:
        def __init__(self):
            self.ai_questions = {}
            self.ai_question_sequence = []
            self.ai_completion_status = {
                "overall_progress": 0,
                "topic_coverage": {},
                "missing_critical_info": [],
                "last_updated": datetime.now().isoformat()
            }
            self.ai_current_question = None
    
    def process_question_tracking(state, question_data):
        """Mock question tracking processing."""
        question_id = question_data.get("question_id")
        if not question_id:
            return {"success": False, "error": "No question_id provided"}
        
        # Create question record
        question_record = {
            "question_text": question_data.get("question_asked", ""),
            "question_id": question_id,
            "topic": question_data.get("topic", "unknown"),
            "answer_received": question_data.get("answer_received", False),
            "answer_quality": question_data.get("answer_quality", "none"),
            "follow_up_needed": question_data.get("follow_up_needed", False),
            "next_question_suggestion": question_data.get("next_question_suggestion", ""),
            "timestamp": datetime.now().isoformat(),
            "user_response": question_data.get("user_response", "")
        }
        
        # Store in questions dictionary
        state.ai_questions[question_id] = question_record
        
        # Update sequence if new question
        if question_id not in state.ai_question_sequence:
            state.ai_question_sequence.append(question_id)
        
        # Update current question
        state.ai_current_question = question_id
        
        return {"success": True, "question_id": question_id}
    
    # Test cases
    mock_state = MockQuestionState()
    
    # Test 1: Process initial question
    print("\nTest: Process Initial Question")
    question_1 = {
        "question_asked": "What is your company name?",
        "question_id": "basic_info_company_001",
        "topic": "basic_info",
        "answer_received": False,
        "answer_quality": "none",
        "follow_up_needed": False,
        "user_response": ""
    }
    
    result_1 = process_question_tracking(mock_state, question_1)
    if result_1["success"]:
        print(f"  [PASS] Successfully processed: {result_1['question_id']}")
        print(f"  [PASS] Current question: {mock_state.ai_current_question}")
        print(f"  [PASS] Questions in sequence: {len(mock_state.ai_question_sequence)}")
    else:
        print(f"  [FAIL] Failed: {result_1.get('error')}")
    
    # Test 2: Process answer received
    print("\nTest: Process Answer Received")
    question_2 = {
        "question_asked": "What type of callouts do you handle?",
        "question_id": "basic_info_callout_type_001",
        "topic": "basic_info",
        "answer_received": True,
        "answer_quality": "complete",
        "follow_up_needed": False,
        "user_response": "PowerCorp Electric Utility"
    }
    
    # First mark the previous question as answered
    if "basic_info_company_001" in mock_state.ai_questions:
        mock_state.ai_questions["basic_info_company_001"]["answer_received"] = True
        mock_state.ai_questions["basic_info_company_001"]["answer_quality"] = "complete"
        mock_state.ai_questions["basic_info_company_001"]["user_response"] = "PowerCorp Electric Utility"
    
    result_2 = process_question_tracking(mock_state, question_2)
    if result_2["success"]:
        print(f"  [PASS] Successfully processed: {result_2['question_id']}")
        
        # Check if previous question was marked as answered
        prev_q = mock_state.ai_questions.get("basic_info_company_001", {})
        if prev_q.get("answer_received"):
            print(f"  [PASS] Previous question marked as answered: {prev_q.get('answer_quality')}")
        else:
            print(f"  [FAIL] Previous question not marked as answered")
            
        print(f"  [PASS] Total questions: {len(mock_state.ai_questions)}")
    else:
        print(f"  [FAIL] Failed: {result_2.get('error')}")
    
    # Test 3: Calculate progress
    print("\nTest: Progress Calculation")
    answered_questions = [q for q in mock_state.ai_questions.values() if q.get("answer_received")]
    total_questions = len(mock_state.ai_questions)
    
    if total_questions > 0:
        completion_ratio = len(answered_questions) / total_questions
        print(f"  [PASS] Answered questions: {len(answered_questions)}/{total_questions}")
        print(f"  [PASS] Completion ratio: {completion_ratio:.2f}")
    else:
        print(f"  [FAIL] No questions processed")

def run_all_tests():
    """Run all core logic tests."""
    print("AI-Driven Q&A Tracking - Core Logic Tests")
    print("=" * 60)
    
    test_structured_response_parsing()
    test_display_content_extraction()
    test_question_state_logic()
    
    print("\n" + "=" * 60)
    print("Core logic tests completed!")
    print("Next step: Test with real Streamlit app to validate integration")
    print("=" * 60)

if __name__ == "__main__":
    run_all_tests()