# modules/topic_tracker.py
import streamlit as st
import json
import re
from config import TOPIC_AREAS, CRITICAL_QUESTIONS

class TopicTracker:
    def __init__(self):
        """Initialize the topic tracker with the predefined topic areas."""
        # Initialize if not already in session state
        if 'topic_areas_covered' not in st.session_state:
            st.session_state.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
    
    def process_topic_update(self, message_content):
        """
        Process topic update messages from the AI.
        Returns True if the message was a topic update, False otherwise.
        """
        if "TOPIC_UPDATE:" not in message_content:
            return False
            
        try:
            # Extract the JSON part after TOPIC_UPDATE:
            json_str = message_content.split("TOPIC_UPDATE:")[1].strip()
            # Sometimes the AI might add additional text after the JSON
            json_str = json_str.split("\n")[0].strip()
            
            # Log the extracted string for debugging
            print(f"Extracted JSON string: {json_str}")
            
            topic_updates = json.loads(json_str)
            
            # Update the session state
            for topic, status in topic_updates.items():
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = status
                    print(f"Updated topic {topic} to {status}")
            
            # After updating topics, check for completion
            self._check_completion_status()
            
            # Check for missing critical questions
            self._check_critical_questions()
            
            return True
        except Exception as e:
            print(f"Error processing topic update: {e}")
            # If there's an error, still return True to avoid displaying the message
            return True
    
    def _check_completion_status(self):
        """Check if all topics are covered and trigger appropriate actions."""
        # Count covered topics
        covered_count = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        
        # If we're near completion (7+ topics covered), check for missing topics
        if covered_count >= 7:
            missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
            if missing_topics:
                # Add system message to explicitly ask about missing topics
                missing_topics_str = ", ".join([TOPIC_AREAS[t] for t in missing_topics])
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": f"IMPORTANT: The following topics have not been covered yet: {missing_topics_str}. Focus your next questions specifically on these topics until all are covered."
                })
                print(f"Added system message about missing topics: {missing_topics_str}")
    
    def _check_critical_questions(self):
        """Check if critical questions for covered topics have been asked."""
        # Get all conversation text
        conversation_text = " ".join([
            msg.get("content", "") for msg in st.session_state.chat_history 
            if isinstance(msg, dict) and msg.get("role") in ["assistant", "user"]
        ]).lower()
        
        # Check each covered topic for its critical questions
        for topic, is_covered in st.session_state.topic_areas_covered.items():
            if is_covered and topic in CRITICAL_QUESTIONS:
                missing_questions = []
                
                for question in CRITICAL_QUESTIONS[topic]:
                    # Check if this critical question has been asked
                    if question.lower() not in conversation_text:
                        missing_questions.append(question)
                
                if missing_questions:
                    # Add a system message to ask these questions
                    question_str = ", ".join(missing_questions)
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": f"IMPORTANT: Although the {TOPIC_AREAS[topic]} topic is marked as covered, you have not specifically asked about: {question_str}. Please ask about these points before moving to other topics."
                    })
    
    def check_summary_readiness(self):
        """
        Check if the questionnaire is ready for summary generation.
        Returns dict with readiness status and any missing topics/questions.
        """
        # Check if all topics are covered
        all_topics_covered = all(st.session_state.topic_areas_covered.values())
        
        if not all_topics_covered:
            missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
            return {
                "ready": False,
                "missing_topics": missing_topics,
                "message": f"The following topics still need to be covered: {', '.join(missing_topics)}"
            }
        
        # Check for missing critical questions
        conversation_text = " ".join([
            msg.get("content", "") for msg in st.session_state.chat_history 
            if isinstance(msg, dict) and msg.get("role") in ["assistant", "user"]
        ]).lower()
        
        missing_critical_questions = []
        
        # Key phrases that should appear in a complete conversation
        key_phrases = [
            "why do you call first", "how many devices", "which device is called first",
            "attributes other than job classification", "straight down the list", "skip around",
            "pauses between calls", "offer positions to people not normally", "call the whole list again",
            "always handle insufficient staffing", "situations where you handle differently",
            "rules that excuse declined callouts"
        ]
        
        for phrase in key_phrases:
            if phrase not in conversation_text:
                missing_critical_questions.append(phrase)
        
        if missing_critical_questions:
            return {
                "ready": False,
                "missing_questions": missing_critical_questions,
                "message": f"The following important points still need to be addressed: {', '.join(missing_critical_questions)}"
            }
        
        # All topics and critical questions covered
        return {
            "ready": True,
            "message": "All topics and critical questions have been covered. Ready for summary."
        }
    
    def get_progress_percentage(self):
        """Calculate the current progress percentage based on topic coverage."""
        covered_topics = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        return int((covered_topics / total_topics) * 100)
    
    def get_progress_data(self):
        """Get detailed progress data for UI display."""
        covered_topics = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        
        return {
            "percentage": int((covered_topics / total_topics) * 100),
            "covered_count": covered_topics,
            "total_count": total_topics,
            "covered_topics": [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if v],
            "missing_topics": [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
        }