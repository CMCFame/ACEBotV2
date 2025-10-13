# modules/question_tracker.py
import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from config import TOPIC_AREAS

class QuestionTracker:
    """
    AI-driven question tracking system that manages questions and answers
    based on AI's structured responses rather than static question mapping.
    """
    
    def __init__(self):
        """Initialize the AI-driven question tracker."""
        self._initialize_session_state()
    
    def _initialize_session_state(self):
        """Initialize session state variables for question tracking."""
        if 'ai_questions' not in st.session_state:
            st.session_state.ai_questions = {}
        
        if 'ai_question_sequence' not in st.session_state:
            st.session_state.ai_question_sequence = []
            
        if 'ai_completion_status' not in st.session_state:
            st.session_state.ai_completion_status = {
                "overall_progress": 0,
                "topic_coverage": {topic: False for topic in TOPIC_AREAS.keys()},
                "missing_critical_info": [],
                "last_updated": datetime.now().isoformat()
            }
            
        if 'ai_current_question' not in st.session_state:
            st.session_state.ai_current_question = None
    
    def process_ai_response(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process structured AI response and update question tracking state.
        
        Args:
            structured_data: Parsed structured response from AI
            
        Returns:
            Processing result with status and any updates made
        """
        result = {
            "success": True,
            "updates_made": [],
            "warnings": [],
            "errors": []
        }
        
        try:
            # Process question tracking data
            if structured_data.get("question_tracking"):
                question_result = self._process_question_tracking(structured_data["question_tracking"])
                result["updates_made"].extend(question_result.get("updates", []))
                result["warnings"].extend(question_result.get("warnings", []))
            
            # Process completion status data
            if structured_data.get("completion_status"):
                completion_result = self._process_completion_status(structured_data["completion_status"])
                result["updates_made"].extend(completion_result.get("updates", []))
                result["warnings"].extend(completion_result.get("warnings", []))
            
            # Update last processed timestamp
            st.session_state.ai_completion_status["last_updated"] = datetime.now().isoformat()
            result["updates_made"].append("Updated timestamp")
            
        except Exception as e:
            result["success"] = False
            result["errors"].append(f"Error processing AI response: {str(e)}")
            print(f"QuestionTracker error: {e}")
        
        return result
    
    def _process_question_tracking(self, question_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process question tracking data from AI response."""
        result = {"updates": [], "warnings": []}
        
        try:
            question_id = question_data.get("question_id")
            if not question_id:
                result["warnings"].append("No question_id provided in question tracking")
                return result
            
            # Update or create question record
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
            st.session_state.ai_questions[question_id] = question_record
            
            # Update sequence if this is a new question
            if question_id not in st.session_state.ai_question_sequence:
                st.session_state.ai_question_sequence.append(question_id)
                result["updates"].append(f"Added new question to sequence: {question_id}")
            else:
                result["updates"].append(f"Updated existing question: {question_id}")
            
            # Update current question
            st.session_state.ai_current_question = question_id
            
            # Log question details for debugging
            print(f"Processed question: {question_id}, answered: {question_record['answer_received']}, quality: {question_record['answer_quality']}")
            
        except Exception as e:
            result["warnings"].append(f"Error processing question tracking: {str(e)}")
        
        return result
    
    def _process_completion_status(self, completion_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process completion status data from AI response."""
        result = {"updates": [], "warnings": []}
        
        try:
            # Update overall progress
            if "overall_progress" in completion_data:
                old_progress = st.session_state.ai_completion_status["overall_progress"]
                new_progress = completion_data["overall_progress"]
                
                if isinstance(new_progress, (int, float)) and 0 <= new_progress <= 100:
                    st.session_state.ai_completion_status["overall_progress"] = new_progress
                    result["updates"].append(f"Progress updated: {old_progress}% → {new_progress}%")
                else:
                    result["warnings"].append(f"Invalid progress value: {new_progress}")
            
            # Update topic coverage
            if "topic_coverage" in completion_data:
                topic_updates = completion_data["topic_coverage"]
                for topic, status in topic_updates.items():
                    if topic in st.session_state.ai_completion_status["topic_coverage"]:
                        old_status = st.session_state.ai_completion_status["topic_coverage"][topic]
                        st.session_state.ai_completion_status["topic_coverage"][topic] = status
                        if old_status != status:
                            result["updates"].append(f"Topic {topic}: {old_status} → {status}")
            
            # Update missing critical info
            if "missing_critical_info" in completion_data:
                missing_info = completion_data["missing_critical_info"]
                if isinstance(missing_info, list):
                    st.session_state.ai_completion_status["missing_critical_info"] = missing_info
                    result["updates"].append(f"Updated missing info list: {len(missing_info)} items")
            
            # Check for completion
            if "current_topic_complete" in completion_data:
                if completion_data["current_topic_complete"]:
                    result["updates"].append("Current topic marked as complete")
            
        except Exception as e:
            result["warnings"].append(f"Error processing completion status: {str(e)}")
        
        return result
    
    def get_answered_questions(self) -> List[Dict[str, Any]]:
        """Get list of questions that have been answered."""
        answered = []
        
        for question_id, question_data in st.session_state.ai_questions.items():
            if question_data.get("answer_received", False):
                answered.append({
                    "question_id": question_id,
                    "question_text": question_data.get("question_text", ""),
                    "topic": question_data.get("topic", "unknown"),
                    "answer_quality": question_data.get("answer_quality", "none"),
                    "timestamp": question_data.get("timestamp", "")
                })
        
        return answered
    
    def get_unanswered_questions(self) -> List[Dict[str, Any]]:
        """Get list of questions that still need answers."""
        unanswered = []
        
        for question_id, question_data in st.session_state.ai_questions.items():
            if not question_data.get("answer_received", False):
                unanswered.append({
                    "question_id": question_id,
                    "question_text": question_data.get("question_text", ""),
                    "topic": question_data.get("topic", "unknown"),
                    "follow_up_needed": question_data.get("follow_up_needed", False)
                })
        
        return unanswered
    
    def get_progress_data(self) -> Dict[str, Any]:
        """Get comprehensive progress data for UI display."""
        answered_questions = self.get_answered_questions()
        total_questions = len(st.session_state.ai_questions)
        
        # Calculate quality-weighted progress
        quality_weights = {"complete": 1.0, "partial": 0.7, "unclear": 0.3, "none": 0.0}
        quality_score = 0
        
        for q in answered_questions:
            quality = q.get("answer_quality", "none")
            quality_score += quality_weights.get(quality, 0)
        
        quality_weighted_progress = (quality_score / max(total_questions, 1)) * 100 if total_questions > 0 else 0
        
        return {
            "ai_driven_progress": st.session_state.ai_completion_status["overall_progress"],
            "quality_weighted_progress": int(quality_weighted_progress),
            "questions_asked": total_questions,
            "questions_answered": len(answered_questions),
            "completion_ratio": len(answered_questions) / max(total_questions, 1) if total_questions > 0 else 0,
            "topic_coverage": st.session_state.ai_completion_status["topic_coverage"],
            "missing_critical_info": st.session_state.ai_completion_status["missing_critical_info"],
            "current_question_id": st.session_state.ai_current_question,
            "last_updated": st.session_state.ai_completion_status["last_updated"]
        }
    
    def is_ready_for_summary(self) -> Dict[str, Any]:
        """Check if questionnaire is ready for summary based on AI assessment."""
        progress_data = self.get_progress_data()
        ai_progress = progress_data["ai_driven_progress"]
        quality_progress = progress_data["quality_weighted_progress"]
        missing_info = progress_data["missing_critical_info"]
        
        # AI says we're done
        if ai_progress >= 95:
            return {
                "ready": True,
                "reason": "ai_completion",
                "message": f"AI assessment indicates {ai_progress}% completion. Ready for summary."
            }
        
        # Good coverage with high quality responses
        if ai_progress >= 85 and quality_progress >= 80:
            return {
                "ready": True,
                "reason": "quality_threshold",
                "message": f"High quality coverage achieved ({quality_progress}% quality score)."
            }
        
        # Reasonable coverage and no critical missing info
        if ai_progress >= 75 and len(missing_info) == 0:
            return {
                "ready": True,
                "reason": "sufficient_coverage",
                "message": f"Sufficient coverage ({ai_progress}%) with no critical gaps identified."
            }
        
        # Not ready yet
        reason_details = []
        if ai_progress < 75:
            reason_details.append(f"Only {ai_progress}% complete")
        if missing_info:
            reason_details.append(f"Missing: {', '.join(missing_info[:3])}")
        
        return {
            "ready": False,
            "reason": "insufficient_coverage",
            "message": f"Need more information. {'; '.join(reason_details)}",
            "missing_info": missing_info,
            "current_progress": ai_progress
        }
    
    def get_current_question_context(self) -> Optional[Dict[str, Any]]:
        """Get context about the current question being discussed."""
        current_id = st.session_state.ai_current_question
        if not current_id or current_id not in st.session_state.ai_questions:
            return None
        
        return st.session_state.ai_questions[current_id]
    
    def get_qa_pairs_for_export(self) -> List[tuple]:
        """Get question-answer pairs formatted for export."""
        qa_pairs = []
        
        for question_id in st.session_state.ai_question_sequence:
            if question_id in st.session_state.ai_questions:
                q_data = st.session_state.ai_questions[question_id]
                if q_data.get("answer_received", False) and q_data.get("user_response"):
                    qa_pairs.append((
                        q_data.get("question_text", ""),
                        q_data.get("user_response", "")
                    ))
        
        return qa_pairs
    
    def debug_status(self) -> Dict[str, Any]:
        """Get debug information about the current tracking state."""
        return {
            "total_questions": len(st.session_state.ai_questions),
            "question_sequence_length": len(st.session_state.ai_question_sequence),
            "current_question": st.session_state.ai_current_question,
            "completion_status": st.session_state.ai_completion_status,
            "recent_questions": list(st.session_state.ai_question_sequence[-5:]),
            "answered_count": len(self.get_answered_questions()),
            "unanswered_count": len(self.get_unanswered_questions())
        }