#!/usr/bin/env python3
"""
Test script for the new reframed questionnaire structure
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from simple_ace_app import ACE_QUESTIONS

def test_questionnaire_structure():
    """Test the basic structure of the new questionnaire"""
    print("Testing New Questionnaire Structure")
    print("=" * 50)
    
    # Test basic structure
    assert len(ACE_QUESTIONS) == 23, f"Expected 23 questions, got {len(ACE_QUESTIONS)}"
    print(f"[OK] Question count: {len(ACE_QUESTIONS)}")
    
    # Test topics
    topics = set(q['topic'] for q in ACE_QUESTIONS)
    expected_topics = {
        "Basic Information", 
        "Contact Process", 
        "List Management", 
        "Insufficient Staffing", 
        "Additional Rules"
    }
    assert topics == expected_topics, f"Topics mismatch. Expected: {expected_topics}, Got: {topics}"
    print(f"[OK] Topics: {sorted(topics)}")
    
    # Test tiers
    tiers = set(q['tier'] for q in ACE_QUESTIONS)
    expected_tiers = {1, 2}
    assert tiers == expected_tiers, f"Tiers mismatch. Expected: {expected_tiers}, Got: {tiers}"
    print(f"[OK] Tiers: {sorted(tiers)}")
    
    # Test tier distribution
    tier1_count = len([q for q in ACE_QUESTIONS if q['tier'] == 1])
    tier2_count = len([q for q in ACE_QUESTIONS if q['tier'] == 2])
    print(f"[OK] Tier 1 questions: {tier1_count}")
    print(f"[OK] Tier 2 questions: {tier2_count}")
    
    # Should be 18 Tier 1 and 5 Tier 2 now (removed 1 Tier 1 question)
    assert tier1_count == 18, f"Expected 18 Tier 1 questions, got {tier1_count}"
    assert tier2_count == 5, f"Expected 5 Tier 2 questions, got {tier2_count}"
    
    # Print topic breakdown
    print("\nTopic Breakdown:")
    for topic in sorted(expected_topics):
        topic_questions = [q for q in ACE_QUESTIONS if q['topic'] == topic]
        tier1 = len([q for q in topic_questions if q['tier'] == 1])
        tier2 = len([q for q in topic_questions if q['tier'] == 2])
        print(f"  {topic}: {len(topic_questions)} total (Tier 1: {tier1}, Tier 2: {tier2})")
    
    print("\n[OK] All tests passed!")
    return True

def show_sample_questions():
    """Display sample questions from each topic"""
    print("\nSample Questions by Topic:")
    print("=" * 50)
    
    topics = {}
    for q in ACE_QUESTIONS:
        topic = q['topic']
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(q)
    
    for topic, questions in sorted(topics.items()):
        print(f"\n{topic} ({len(questions)} questions):")
        # Show first question as example
        first_q = questions[0]
        print(f"   Example: Q{first_q['id']}: {first_q['text']}")

if __name__ == "__main__":
    try:
        test_questionnaire_structure()
        show_sample_questions()
        print("\nQuestionnaire is ready for deployment!")
        
    except Exception as e:
        print(f"Test failed: {str(e)}")
        sys.exit(1)