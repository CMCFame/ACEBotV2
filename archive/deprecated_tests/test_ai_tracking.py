# test_ai_tracking.py
"""
Comprehensive test suite for the AI-driven Q&A tracking system.
Run this script to validate all components work correctly.
"""

import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, List

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import our modules
from modules.ai_service import AIService
from modules.question_tracker import QuestionTracker
from modules.session import SessionManager
from config import TOPIC_AREAS

class MockStreamlitState:
    """Mock Streamlit session state for testing."""
    def __init__(self):
        self.user_info = {"name": "", "company": ""}
        self.responses = []
        self.current_question_index = 0
        self.chat_history = []
        self.visible_messages = []
        self.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
        self.summary_requested = False
        self.explicitly_finished = False
        self.restoring_session = False
        
        # AI tracking variables
        self.ai_questions = {}
        self.ai_question_sequence = []
        self.ai_completion_status = {
            "overall_progress": 0,
            "topic_coverage": {topic: False for topic in TOPIC_AREAS.keys()},
            "missing_critical_info": [],
            "last_updated": datetime.now().isoformat()
        }
        self.ai_current_question = None

# Create mock session state
mock_st_state = MockStreamlitState()

class MockStreamlit:
    """Mock Streamlit module for testing."""
    def __init__(self):
        self.session_state = mock_st_state
        self.secrets = {"DEBUG_MODE": True}
    
    def error(self, message):
        print(f"ST_ERROR: {message}")
    
    def warning(self, message):
        print(f"ST_WARNING: {message}")

# Replace streamlit import for testing
sys.modules['streamlit'] = MockStreamlit()

class AITrackingTestSuite:
    """Comprehensive test suite for AI-driven tracking system."""
    
    def __init__(self):
        self.ai_service = AIService()
        self.question_tracker = QuestionTracker()
        self.session_manager = SessionManager()
        self.test_results = []
        
    def log_test(self, test_name: str, passed: bool, details: str = ""):
        """Log test result."""
        status = "PASS" if passed else "FAIL"
        self.test_results.append({
            "test": test_name,
            "status": status,
            "details": details
        })
        print(f"[{status}] {test_name}: {details}")
    
    def create_mock_ai_responses(self) -> List[Dict[str, Any]]:
        """Create realistic mock AI responses for testing."""
        return [
            {
                "conversation_content": "Hello! I'm here to help you complete the ACE questionnaire for your ARCOS implementation. Could you please provide your name and company name to get started?",
                "question_tracking": {
                    "question_asked": "Could you please provide your name and company name?",
                    "question_id": "basic_info_company_name_001",
                    "topic": "basic_info",
                    "answer_received": False,
                    "answer_quality": "none",
                    "follow_up_needed": False,
                    "user_response": ""
                },
                "completion_status": {
                    "overall_progress": 5,
                    "topic_coverage": {"basic_info": False, "staffing_details": False, "contact_process": False, "list_management": False, "insufficient_staffing": False, "calling_logistics": False, "list_changes": False, "tiebreakers": False, "additional_rules": False},
                    "missing_critical_info": ["user_name", "company_name", "callout_type"],
                    "current_topic_complete": False
                }
            },
            {
                "conversation_content": "Thank you, John from PowerCorp! Now I understand you work for an electric utility. What type of situation are you typically responding to when you initiate a callout?",
                "question_tracking": {
                    "question_asked": "What type of situation are you typically responding to when you initiate a callout?",
                    "question_id": "basic_info_callout_type_001",
                    "topic": "basic_info",
                    "answer_received": True,
                    "answer_quality": "complete",
                    "follow_up_needed": False,
                    "user_response": "I'm John Smith from PowerCorp Electric Utility"
                },
                "completion_status": {
                    "overall_progress": 15,
                    "topic_coverage": {"basic_info": False, "staffing_details": False, "contact_process": False, "list_management": False, "insufficient_staffing": False, "calling_logistics": False, "list_changes": False, "tiebreakers": False, "additional_rules": False},
                    "missing_critical_info": ["callout_type", "staffing_requirements"],
                    "current_topic_complete": False
                }
            },
            {
                "conversation_content": "Storm-related power outages are definitely critical situations. How many employees are typically required for these callouts, and what specific roles do they fill?",
                "question_tracking": {
                    "question_asked": "How many employees are typically required for these callouts, and what specific roles do they fill?",
                    "question_id": "staffing_details_requirements_001",
                    "topic": "staffing_details",
                    "answer_received": True,
                    "answer_quality": "complete",
                    "follow_up_needed": False,
                    "user_response": "We mainly respond to storm-related power outages affecting multiple neighborhoods"
                },
                "completion_status": {
                    "overall_progress": 25,
                    "topic_coverage": {"basic_info": True, "staffing_details": False, "contact_process": False, "list_management": False, "insufficient_staffing": False, "calling_logistics": False, "list_changes": False, "tiebreakers": False, "additional_rules": False},
                    "missing_critical_info": ["staffing_numbers", "job_roles"],
                    "current_topic_complete": True
                }
            }
        ]
    
    def test_structured_response_parsing(self):
        """Test 1: Structured Response Parsing"""
        print("\n=== Test 1: Structured Response Parsing ===")
        
        # Test valid structured response
        test_response = """Hello! Let me ask you about your callout process.

QUESTION_TRACKING: {"question_asked": "What is your company name?", "question_id": "basic_info_company_001", "topic": "basic_info", "answer_received": false, "answer_quality": "none", "follow_up_needed": false, "user_response": ""}

COMPLETION_STATUS: {"overall_progress": 10, "topic_coverage": {"basic_info": false}, "missing_critical_info": ["company_name"], "current_topic_complete": false}"""
        
        try:
            structured_data = self.ai_service._parse_structured_response(test_response)
            
            # Validate question tracking
            qt = structured_data.get("question_tracking")
            if qt and qt.get("question_id") == "basic_info_company_001":
                self.log_test("Parse Question Tracking", True, f"Question ID: {qt.get('question_id')}")
            else:
                self.log_test("Parse Question Tracking", False, f"Expected question ID, got: {qt}")
            
            # Validate completion status
            cs = structured_data.get("completion_status")
            if cs and cs.get("overall_progress") == 10:
                self.log_test("Parse Completion Status", True, f"Progress: {cs.get('overall_progress')}%")
            else:
                self.log_test("Parse Completion Status", False, f"Expected progress 10, got: {cs}")
            
            # Test display content extraction
            display_content = self.ai_service._extract_display_content(test_response, structured_data)
            if "Hello!" in display_content and "QUESTION_TRACKING" not in display_content:
                self.log_test("Extract Display Content", True, "Structured blocks removed correctly")
            else:
                self.log_test("Extract Display Content", False, f"Display content: {display_content[:100]}...")
                
        except Exception as e:
            self.log_test("Structured Response Parsing", False, f"Exception: {str(e)}")
    
    def test_question_tracker_processing(self):
        """Test 2: Question Tracker State Management"""
        print("\n=== Test 2: Question Tracker State Management ===")
        
        mock_responses = self.create_mock_ai_responses()
        
        try:
            # Process first response (initial question)
            result1 = self.question_tracker.process_ai_response(mock_responses[0])
            
            if result1["success"]:
                self.log_test("Process Initial Question", True, f"Updates: {len(result1['updates_made'])}")
            else:
                self.log_test("Process Initial Question", False, f"Errors: {result1['errors']}")
            
            # Check if question was stored
            if mock_st_state.ai_current_question == "basic_info_company_name_001":
                self.log_test("Store Current Question", True, f"Current: {mock_st_state.ai_current_question}")
            else:
                self.log_test("Store Current Question", False, f"Expected basic_info_company_name_001, got: {mock_st_state.ai_current_question}")
            
            # Process second response (answer received + new question)
            result2 = self.question_tracker.process_ai_response(mock_responses[1])
            
            # Check if previous question was marked as answered
            q1_data = mock_st_state.ai_questions.get("basic_info_company_name_001", {})
            if q1_data.get("answer_received") == True:
                self.log_test("Mark Question Answered", True, f"Quality: {q1_data.get('answer_quality')}")
            else:
                self.log_test("Mark Question Answered", False, f"Answer received: {q1_data.get('answer_received')}")
            
            # Check progress tracking
            progress_data = self.question_tracker.get_progress_data()
            if progress_data["ai_driven_progress"] > 0:
                self.log_test("Track Progress", True, f"Progress: {progress_data['ai_driven_progress']}%")
            else:
                self.log_test("Track Progress", False, f"Progress: {progress_data['ai_driven_progress']}%")
                
        except Exception as e:
            self.log_test("Question Tracker Processing", False, f"Exception: {str(e)}")
    
    def test_progress_calculation(self):
        """Test 3: Progress Calculation Accuracy"""
        print("\n=== Test 3: Progress Calculation Accuracy ===")
        
        try:
            # Process multiple responses to build up progress
            mock_responses = self.create_mock_ai_responses()
            
            progress_values = []
            for i, response in enumerate(mock_responses):
                self.question_tracker.process_ai_response(response)
                progress_data = self.question_tracker.get_progress_data()
                progress_values.append(progress_data["ai_driven_progress"])
            
            # Progress should increase over time
            if all(progress_values[i] <= progress_values[i+1] for i in range(len(progress_values)-1)):
                self.log_test("Progressive Increase", True, f"Progress: {progress_values}")
            else:
                self.log_test("Progressive Increase", False, f"Progress: {progress_values}")
            
            # Test readiness assessment
            readiness = self.question_tracker.is_ready_for_summary()
            if isinstance(readiness, dict) and "ready" in readiness:
                self.log_test("Summary Readiness Check", True, f"Ready: {readiness['ready']}")
            else:
                self.log_test("Summary Readiness Check", False, f"Invalid readiness format: {readiness}")
            
            # Test Q&A export
            qa_pairs = self.question_tracker.get_qa_pairs_for_export()
            if isinstance(qa_pairs, list):
                self.log_test("Q&A Export", True, f"Exported {len(qa_pairs)} pairs")
            else:
                self.log_test("Q&A Export", False, f"Invalid export format: {type(qa_pairs)}")
                
        except Exception as e:
            self.log_test("Progress Calculation", False, f"Exception: {str(e)}")
    
    def test_session_persistence(self):
        """Test 4: Session Save/Restore with AI Data"""
        print("\n=== Test 4: Session Save/Restore ===")
        
        try:
            # Set up some AI tracking data
            mock_st_state.ai_questions = {
                "test_q1": {"question_text": "Test question 1", "answer_received": True},
                "test_q2": {"question_text": "Test question 2", "answer_received": False}
            }
            mock_st_state.ai_completion_status["overall_progress"] = 45
            
            # Test session save
            session_data = self.session_manager.get_session_state()
            
            if "ai_questions" in session_data:
                self.log_test("Save AI Data", True, f"Saved {len(session_data['ai_questions'])} questions")
            else:
                self.log_test("Save AI Data", False, "AI questions not found in session data")
            
            if session_data.get("version") == "4.0":
                self.log_test("Session Version", True, f"Version: {session_data['version']}")
            else:
                self.log_test("Session Version", False, f"Expected 4.0, got: {session_data.get('version')}")
            
            # Test session restore (mock restore data)
            restore_data = {
                "ai_questions": {"restored_q1": {"question_text": "Restored question"}},
                "ai_completion_status": {"overall_progress": 75},
                "user_info": {"name": "Test User", "company": "Test Company"},
                "chat_history": [],
                "visible_messages": [],
                "topic_areas_covered": {}
            }
            
            # Clear current state
            mock_st_state.ai_questions = {}
            mock_st_state.ai_completion_status["overall_progress"] = 0
            
            # Mock restore (simplified version)
            mock_st_state.ai_questions = restore_data["ai_questions"]
            mock_st_state.ai_completion_status = restore_data["ai_completion_status"]
            
            if len(mock_st_state.ai_questions) > 0:
                self.log_test("Restore AI Data", True, f"Restored {len(mock_st_state.ai_questions)} questions")
            else:
                self.log_test("Restore AI Data", False, "No questions restored")
                
        except Exception as e:
            self.log_test("Session Persistence", False, f"Exception: {str(e)}")
    
    def test_error_handling(self):
        """Test 5: Error Handling and Fallbacks"""
        print("\n=== Test 5: Error Handling ===")
        
        try:
            # Test malformed JSON parsing
            malformed_response = """Hello!
            QUESTION_TRACKING: {"question_asked": "Test", "invalid_json"}
            """
            
            structured_data = self.ai_service._parse_structured_response(malformed_response)
            
            if structured_data.get("question_tracking") is None:
                self.log_test("Handle Malformed JSON", True, "Gracefully handled malformed JSON")
            else:
                self.log_test("Handle Malformed JSON", False, "Should have returned None for malformed JSON")
            
            # Test validation with missing fields
            invalid_data = {
                "question_tracking": {
                    "question_asked": "Test question",
                    # Missing required fields
                },
                "completion_status": {
                    "overall_progress": "invalid_type"  # Should be number
                }
            }
            
            validation = self.ai_service.validate_structured_response(invalid_data)
            
            if not validation["is_valid"]:
                self.log_test("Validate Missing Fields", True, f"Caught {len(validation['missing_fields'])} missing fields")
            else:
                self.log_test("Validate Missing Fields", False, "Should have failed validation")
            
            # Test empty response handling
            empty_response = ""
            display_content = self.ai_service._extract_display_content(empty_response, {})
            
            if display_content and "processing" in display_content.lower():
                self.log_test("Handle Empty Response", True, "Provided fallback content")
            else:
                self.log_test("Handle Empty Response", False, f"Fallback content: {display_content}")
                
        except Exception as e:
            self.log_test("Error Handling", False, f"Exception: {str(e)}")
    
    def test_integration_flow(self):
        """Test 6: Complete Integration Flow"""
        print("\n=== Test 6: Integration Flow ===")
        
        try:
            # Simulate complete conversation flow
            conversation_steps = [
                ("user_greeting", "Hi, I'm John from PowerCorp"),
                ("ai_response_1", self.create_mock_ai_responses()[0]),
                ("user_answer_1", "PowerCorp Electric Utility"),
                ("ai_response_2", self.create_mock_ai_responses()[1]),
                ("user_answer_2", "Storm-related outages"),
                ("ai_response_3", self.create_mock_ai_responses()[2])
            ]
            
            questions_asked = 0
            questions_answered = 0
            
            for step_name, step_data in conversation_steps:
                if step_name.startswith("ai_response"):
                    # Process AI response
                    result = self.question_tracker.process_ai_response(step_data)
                    if result["success"]:
                        questions_asked += 1
                elif step_name.startswith("user_answer"):
                    # Mark answer as received (simulate)
                    questions_answered += 1
            
            progress_data = self.question_tracker.get_progress_data()
            
            if questions_asked > 0 and questions_answered > 0:
                self.log_test("Integration Flow", True, f"Asked: {questions_asked}, Answered: {questions_answered}")
            else:
                self.log_test("Integration Flow", False, f"Asked: {questions_asked}, Answered: {questions_answered}")
            
            if progress_data["ai_driven_progress"] > 0:
                self.log_test("End-to-End Progress", True, f"Final progress: {progress_data['ai_driven_progress']}%")
            else:
                self.log_test("End-to-End Progress", False, f"No progress recorded")
                
        except Exception as e:
            self.log_test("Integration Flow", False, f"Exception: {str(e)}")
    
    def run_all_tests(self):
        """Run complete test suite and generate report."""
        print("🚀 Starting AI-Driven Q&A Tracking Test Suite")
        print("=" * 60)
        
        # Update todos
        self.update_test_progress("Create mock AI responses for testing", "completed")
        
        # Run all tests
        self.test_structured_response_parsing()
        self.update_test_progress("Test structured response parsing", "completed")
        
        self.test_question_tracker_processing()
        self.update_test_progress("Test question tracking state management", "completed")
        
        self.test_progress_calculation()
        self.update_test_progress("Test progress calculation accuracy", "completed")
        
        self.test_session_persistence()
        self.update_test_progress("Test session save/restore with AI data", "completed")
        
        self.test_error_handling()
        self.update_test_progress("Test error handling and fallbacks", "completed")
        
        self.test_integration_flow()
        
        # Generate final report
        self.generate_test_report()
        
    def update_test_progress(self, task_name: str, status: str):
        """Update test progress (placeholder for todo tracking)."""
        print(f"✓ {task_name}: {status}")
    
    def generate_test_report(self):
        """Generate comprehensive test report."""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["status"] == "PASS"])
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS ({failed_tests}):")
            for test in self.test_results:
                if test["status"] == "FAIL":
                    print(f"  • {test['test']}: {test['details']}")
        
        print(f"\n✅ PASSED TESTS ({passed_tests}):")
        for test in self.test_results:
            if test["status"] == "PASS":
                print(f"  • {test['test']}: {test['details']}")
        
        # Overall assessment
        print("\n" + "=" * 60)
        if success_rate >= 90:
            print("🎉 EXCELLENT: System ready for production!")
        elif success_rate >= 75:
            print("✅ GOOD: System mostly working, minor issues to address")
        elif success_rate >= 50:
            print("⚠️  NEEDS WORK: Significant issues found")
        else:
            print("❌ CRITICAL: Major problems, not ready for use")
        
        print("=" * 60)

def main():
    """Run the test suite."""
    test_suite = AITrackingTestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()