# test_answer_tracking.py
"""
Test to verify answer tracking works correctly
"""

def test_conversation_flow():
    """Test that simulates the expected conversation flow based on your experience"""
    print("=== Testing Answer Tracking Flow ===")
    
    # Expected conversation flow based on ACE questionnaire
    expected_questions = [
        {"id": "basic_info_user_company_001", "text": "Could you please provide your name and company name?"},
        {"id": "basic_info_callout_type_001", "text": "What type of situation are you responding to for this callout?"},
        {"id": "basic_info_frequency_001", "text": "How frequently do these callouts occur?"},
        {"id": "staffing_number_001", "text": "How many employees are typically required for the callout?"},
        {"id": "contact_first_person_001", "text": "Who do you call first and why?"},
        {"id": "contact_devices_001", "text": "How many devices do they have?"},
    ]
    
    # Simulate user responses
    user_responses = [
        "Victor - ACME",
        "We typically respond to power outages caused by severe weather events like storms or fallen trees. We also get callouts for equipment failures at substations or along power lines.",
        "We typically receive 2-3 emergency callouts per week, with more frequent callouts during severe weather events or peak seasons. On average, this amounts to about 10-15 callouts per month for our utility company.",
        "We typically call the on-duty dispatcher first, who then contacts the appropriate field crew supervisor based on the type of emergency and location. The supervisor is responsible for assembling and dispatching the required team.",
        "We call the on-duty dispatcher first because they have real-time information on crew availability and can quickly assess the urgency of the situation. This allows us to mobilize the right resources efficiently and respond to outages or emergencies as quickly as possible."
    ]
    
    # Track what should be answered
    answered_questions = []
    
    for i, response in enumerate(user_responses):
        if i < len(expected_questions):
            answered_questions.append({
                "question_id": expected_questions[i]["id"],
                "user_response": response,
                "answer_received": True,
                "answer_quality": "complete"
            })
            
            expected_progress = int((len(answered_questions) / len(expected_questions)) * 100)
            
            print(f"\nAfter response {i+1}:")
            print(f"  Question answered: {expected_questions[i]['text']}")
            print(f"  User response: {response[:50]}...")
            print(f"  Expected progress: {expected_progress}%")
            print(f"  Questions answered: {len(answered_questions)}/{len(expected_questions)}")
    
    print(f"\n=== Analysis ===")
    print(f"The issue you're experiencing:")
    print(f"1. AI asks 'Who do you call first?' then separately 'Why?' - should be combined")
    print(f"2. Progress shows 0/5 instead of tracking actual responses")
    print(f"3. AI doesn't recognize when questions are answered")
    
    print(f"\nExpected behavior:")
    print(f"- After 'Victor - ACME': Progress should be ~17% (1/6 questions)")
    print(f"- After callout type response: Progress should be ~33% (2/6 questions)")
    print(f"- AI should ask combined questions like 'Who do you call first and why?'")
    
    return answered_questions

def test_question_format():
    """Test the correct question format based on ACE examples"""
    print("\n=== Testing Question Format ===")
    
    # Based on the ACE examples, these should be the actual questions:
    correct_questions = [
        "Could you please provide your name and company name?",
        "What type of situation are you responding to for this callout?", 
        "How many employees are typically required for the callout?",
        "Who do you call first and why?",  # Combined question, not separate
        "How many devices do they have?",
        "Which device do you call first and why?",  # Combined question
        "What types of devices are you calling?",
        "Is the next employee you call on the same list or a different list?",
        "How many lists total do you use for this callout?",
        "Are each of these lists based on Job Classification or some other attribute?",
    ]
    
    # What the AI is currently doing wrong:
    wrong_behavior = [
        "Asking 'Who do you call first?' then separately 'Why?' - should be one question",
        "Not recognizing answered questions - progress stays at 0/5", 
        "Asking questions not in the original ACE format",
        "Not updating question tracking when user provides answers"
    ]
    
    print("Correct question format:")
    for i, q in enumerate(correct_questions[:5], 1):
        print(f"  {i}. {q}")
    
    print(f"\nCurrent issues:")
    for issue in wrong_behavior:
        print(f"  - {issue}")

if __name__ == "__main__":
    test_conversation_flow()
    test_question_format()
    
    print(f"\n" + "="*50)
    print("SOLUTION NEEDED:")
    print("1. Fix system prompt to use combined questions")
    print("2. Ensure AI recognizes when questions are answered")
    print("3. Update progress tracking to reflect actual responses")
    print("4. Test with a fresh conversation to verify fixes")
    print("="*50)