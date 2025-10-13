#!/usr/bin/env python3
"""
Test script to verify AI system prompt examples
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simple_ace_app import get_question_examples

def test_ai_examples():
    """Test what the AI system prompt will show for examples"""
    print("Testing AI System Prompt Examples")
    print("=" * 50)
    
    # Test examples for a few key questions
    test_questions = [2, 5, 9, 15]
    
    for q_id in test_questions:
        print(f"\nQuestion {q_id} examples:")
        examples = get_question_examples(q_id)
        formatted_examples = ', '.join(examples)
        print(f"AI will see: {formatted_examples[:200]}...")
        print(f"Example quality: {'✓ Good' if all(len(ex) > 80 and 'we' in ex.lower() for ex in examples) else '✗ Needs work'}")
    
    return True

if __name__ == "__main__":
    test_ai_examples()
    print("\nAI examples testing complete!")