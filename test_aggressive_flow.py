#!/usr/bin/env python3
"""
Test script to verify the aggressive question advancement logic
"""

def test_advancement_logic():
    """Test the aggressive advancement conditions"""
    print("Testing Aggressive Question Advancement Logic")
    print("=" * 50)
    
    # Simulate different user responses and check advancement logic
    test_cases = [
        {
            "user_input": "We call the supervisor first",
            "ai_response": "Got it! **What methods do you use to contact them?**",
            "should_advance": True,
            "reason": "Substantive answer, no clarification request"
        },
        {
            "user_input": "help",
            "ai_response": "Example: We use company-issued smartphones first, then personal phones as backup.",
            "should_advance": False,
            "reason": "User requested help"
        },
        {
            "user_input": "We have different approaches depending on the situation",
            "ai_response": "Could you be more specific about what determines which approach you use?",
            "should_advance": False,
            "reason": "AI asking clarification (contains ? and question words)"
        },
        {
            "user_input": "Yes",
            "ai_response": "Perfect! **How many different lists do you use?**",
            "should_advance": False,
            "reason": "Too short response (< 5 characters)"
        },
        {
            "user_input": "We use a rotation system with weekly changes for standby crews",
            "ai_response": "Thanks! **How do you determine the order within each list?**",
            "should_advance": True,
            "reason": "Substantive answer with good detail"
        }
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"\nTest Case {i}:")
        print(f"User Input: '{case['user_input']}'")
        print(f"AI Response: '{case['ai_response']}'")
        
        # Apply the advancement logic
        user_input = case['user_input']
        ai_response = case['ai_response']
        
        user_input_lower = user_input.lower().strip()
        ai_response_lower = ai_response.lower()
        
        # Apply the actual logic from the app
        is_too_short = len(user_input.strip()) < 5
        
        # Updated clarification logic
        has_bold_question = "**" in ai_response
        has_question_mark = "?" in ai_response
        has_clarification_words = any(word in ai_response_lower for word in ["could you elaborate", "can you provide more", "could you be more specific", "what do you mean", "can you clarify"])
        
        is_ai_asking_clarification = (
            has_question_mark and 
            has_clarification_words and
            not has_bold_question  # If there's a bold question, it's likely the next question
        )
        
        is_user_help_request = any(phrase in user_input_lower for phrase in ["example", "help", "?", "what do you mean", "clarify", "explain"])
        
        should_not_advance = (
            is_too_short or 
            is_ai_asking_clarification or 
            is_user_help_request
        )
        
        actual_advance = not should_not_advance
        expected_advance = case['should_advance']
        
        status = "PASS" if actual_advance == expected_advance else "FAIL"
        print(f"Expected Advance: {expected_advance}")
        print(f"Actual Advance: {actual_advance}")
        print(f"Reason: {case['reason']}")
        print(f"Result: {status}")
        
        if actual_advance != expected_advance:
            print(f"  - Too short: {is_too_short}")
            print(f"  - AI clarification: {is_ai_asking_clarification}")
            print(f"  - User help: {is_user_help_request}")
    
    print(f"\n{'='*50}")
    print("Aggressive advancement logic test complete!")
    return True

if __name__ == "__main__":
    test_advancement_logic()