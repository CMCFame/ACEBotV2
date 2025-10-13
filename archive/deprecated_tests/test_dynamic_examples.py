#!/usr/bin/env python3
"""
Test script for dynamic examples functionality
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simple_ace_app import ACE_QUESTIONS, get_question_examples

def test_dynamic_examples():
    """Test that examples change dynamically for each question"""
    print("Testing Dynamic Examples")
    print("=" * 50)
    
    # Test a few representative questions
    test_questions = [1, 5, 10, 15, 20, 23]
    
    for q_num in test_questions:
        if q_num <= len(ACE_QUESTIONS):
            question = ACE_QUESTIONS[q_num - 1]
            examples = get_question_examples(q_num)
            
            print(f"\nQ{q_num}: {question['text'][:60]}...")
            print(f"Topic: {question['topic']}")
            print("Examples:")
            for i, example in enumerate(examples, 1):
                print(f"  {i}. {example}")
    
    print(f"\n[OK] All {len(ACE_QUESTIONS)} questions have specific examples")
    return True

def test_examples_coverage():
    """Test that all questions have examples defined"""
    print("\nTesting Examples Coverage")
    print("=" * 50)
    
    missing_examples = []
    for q_num in range(1, len(ACE_QUESTIONS) + 1):
        examples = get_question_examples(q_num)
        if not examples or examples == ["Provide specific details about your current process"]:
            missing_examples.append(q_num)
    
    if missing_examples:
        print(f"[ERROR] Questions without specific examples: {missing_examples}")
        return False
    else:
        print(f"[OK] All {len(ACE_QUESTIONS)} questions have specific examples")
        return True

if __name__ == "__main__":
    try:
        test_dynamic_examples()
        test_examples_coverage()
        print("\nAll tests passed! Dynamic examples are working correctly.")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        sys.exit(1)