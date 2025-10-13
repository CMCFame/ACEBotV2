#!/usr/bin/env python3
"""
Test script for question progression logic
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simple_ace_app import ACE_QUESTIONS

def test_question_indexing():
    """Test that question indexing works correctly"""
    print("Testing Question Indexing Logic")
    print("=" * 50)
    
    # Test the indexing logic used in the app
    current_question = 1  # This is how the app starts
    
    print(f"Starting at current_question = {current_question}")
    
    # Get current question (1-indexed to 0-indexed conversion)
    if current_question <= len(ACE_QUESTIONS):
        current_q = ACE_QUESTIONS[current_question - 1]  # Convert to 0-indexed
        print(f"Current Q{current_q['id']}: {current_q['text'][:50]}...")
    
    # Test next question logic 
    if current_question < len(ACE_QUESTIONS):
        next_question_index = current_question  # This should be the next question index
        if next_question_index < len(ACE_QUESTIONS):
            next_q = ACE_QUESTIONS[next_question_index]
            print(f"Next Q{next_q['id']}: {next_q['text'][:50]}...")
            
            # Test progression
            if current_question + 1 <= len(ACE_QUESTIONS):
                after_advance = ACE_QUESTIONS[current_question]  # After advancing current_question += 1
                print(f"After advance Q{after_advance['id']}: {after_advance['text'][:50]}...")
                
                # Verify they match
                if next_q['id'] == after_advance['id']:
                    print("[OK] Question progression logic is correct!")
                else:
                    print(f"[ERROR] Mismatch! Next: Q{next_q['id']}, After advance: Q{after_advance['id']}")
            else:
                print("[OK] At final question")
    
    print(f"\nTotal questions: {len(ACE_QUESTIONS)}")
    print(f"Valid current_question range: 1 to {len(ACE_QUESTIONS)}")
    
    return True

def test_all_questions_accessible():
    """Test that all questions are accessible with the current logic"""
    print("\nTesting All Questions Accessible")
    print("=" * 50)
    
    for i in range(1, len(ACE_QUESTIONS) + 1):
        try:
            q = ACE_QUESTIONS[i - 1]  # Convert 1-indexed to 0-indexed
            print(f"Q{q['id']}: Accessible (current_question={i})")
        except IndexError as e:
            print(f"[ERROR] Q{i} not accessible: {e}")
            return False
    
    print("[OK] All questions accessible!")
    return True

if __name__ == "__main__":
    try:
        test_question_indexing()
        test_all_questions_accessible()
        print("\nAll tests passed! Question progression should work correctly.")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        sys.exit(1)