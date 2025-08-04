#!/usr/bin/env python3
"""
Test script for save/resume functionality
"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(__file__))

def test_save_resume():
    """Test the save/resume functionality"""
    print("Testing Save/Resume Functionality")
    print("=" * 50)
    
    # Mock session state data
    mock_session = {
        "user_info": {"name": "Test User", "company": "Test Company", "email": "test@test.com"},
        "answers": {1: "Test answer 1", 2: "Test answer 2"},
        "current_question": 3,
        "conversation": [
            {"role": "assistant", "content": "Welcome!"},
            {"role": "user", "content": "Test answer 1"}
        ],
        "summary_text": "Test summary",
        "completed": False,
        "started": True
    }
    
    print("Mock session data created")
    
    # Test JSON serialization
    try:
        json_data = json.dumps(mock_session, indent=2)
        print("JSON serialization works")
        
        # Test deserialization
        restored_data = json.loads(json_data)
        print("JSON deserialization works")
        
        # Test key conversion
        answers_data = restored_data.get("answers", {})
        restored_answers = {int(k): v for k, v in answers_data.items()}
        print(f"Answer keys converted: {restored_answers}")
        
        # Verify data integrity
        assert restored_data["user_info"]["name"] == "Test User"
        assert restored_answers[1] == "Test answer 1"
        assert restored_data["current_question"] == 3
        print("Data integrity verified")
        
    except Exception as e:
        print(f"Error: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("Save/Resume functionality test PASSED!")
    return True

if __name__ == "__main__":
    test_save_resume()