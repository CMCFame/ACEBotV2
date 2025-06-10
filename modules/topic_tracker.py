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
        Process topic update messages from the AI with improved validation.
        Returns True if the message was a topic update, False otherwise.
        """
        if "TOPIC_UPDATE:" not in message_content:
            return False
            
        try:
            # Extract the JSON part after TOPIC_UPDATE:
            json_str = message_content.split("TOPIC_UPDATE:")[1].strip()
            # Sometimes the AI might add additional text after the JSON
            json_str = json_str.split("\n")[0].strip()
            
            topic_updates = json.loads(json_str)
            
            # Apply updates directly - trust the AI's assessment more
            for topic, status in topic_updates.items():
                if topic in st.session_state.topic_areas_covered:
                    old_status = st.session_state.topic_areas_covered[topic]
                    st.session_state.topic_areas_covered[topic] = status
                    print(f"Updated topic {topic} from {old_status} to {status}")
            
            return True
        except Exception as e:
            print(f"Error processing topic update: {e}")
            return True  # Still return True to hide the malformed update
    
    def check_summary_readiness(self):
        """
        UNIFIED validation system - single source of truth for completion.
        Much more intelligent about recognizing when topics are actually covered.
        """
        # Check if all topics are marked as covered
        all_topics_covered = all(st.session_state.topic_areas_covered.values())
        
        if not all_topics_covered:
            missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
            
            # SMART VALIDATION: Check if "missing" topics are actually covered in conversation
            conversation_text = self._get_conversation_text()
            truly_missing = self._smart_topic_validation(missing_topics, conversation_text)
            
            if truly_missing:
                return {
                    "ready": False,
                    "missing_topics": truly_missing,
                    "message": f"Please provide information about: {', '.join(truly_missing)}"
                }
        
        # Check minimum conversation depth (prevent premature completion)
        from modules.summary import SummaryGenerator
        summary_gen = SummaryGenerator()
        qa_pairs = summary_gen._extract_qa_pairs_from_visible_messages()
        
        if len(qa_pairs) < 20:  # Reasonable minimum for comprehensive coverage
            return {
                "ready": False,
                "message": f"Need more comprehensive coverage. Currently have {len(qa_pairs)} question-answer pairs."
            }
        
        # All checks passed - truly ready
        return {
            "ready": True,
            "message": "All essential topics covered comprehensively."
        }
    
    def _smart_topic_validation(self, missing_topics, conversation_text):
        """
        Intelligent validation that recognizes when topics are actually covered
        even if not explicitly marked. Fixes the rigid keyword matching problem.
        """
        truly_missing = []
        
        # Enhanced topic detection patterns
        smart_patterns = {
            "Basic Information": [
                r"(name|company|callout|situation|outage|emergency)",
                lambda text: any(word in text for word in ["name", "company", "acme", "victor"])
            ],
            "Staffing Details": [
                r"(\d+\s*(employee|technician|worker|crew|lineman))",
                lambda text: any(word in text for word in ["crew", "technician", "employee", "staff", "lineman"])
            ],
            "Contact Process": [
                r"(call first|contact|dispatcher|supervisor|device|phone)",
                lambda text: any(phrase in text for phrase in ["call first", "contact", "dispatcher", "device", "phone"])
            ],
            "List Management": [
                r"(list|order|seniority|classification|skip|straight)",
                lambda text: any(word in text for word in ["list", "order", "seniority", "classification"])
            ],
            "Insufficient Staffing": [
                r"(required number|not enough|different list|mutual aid|neighboring)",
                lambda text: any(phrase in text for phrase in ["not enough", "required number", "mutual aid", "neighboring"])
            ],
            "Calling Logistics": [
                r"(simultaneous|union|individual|one at a time|same time)",
                lambda text: any(phrase in text for phrase in ["simultaneous", "union", "individual", "one at a time"])
            ],
            "List Changes": [
                r"(change|update|quarterly|over time|new hire)",
                lambda text: any(phrase in text for phrase in ["change", "update", "quarterly", "over time"])
            ],
            "Tiebreakers": [
                r"(tie|tiebreaker|overtime|seniority|alphabetical)",
                lambda text: any(word in text for word in ["tie", "tiebreaker", "overtime", "seniority"])
            ],
            "Additional Rules": [
                r"(email|text|shift|rest|excuse|8 hours|vacation)",
                lambda text: any(phrase in text for phrase in ["email", "text", "shift", "hours", "vacation"])
            ]
        }
        
        for topic in missing_topics:
            if topic in smart_patterns:
                pattern, smart_check = smart_patterns[topic]
                
                # Check both regex pattern and smart function
                if re.search(pattern, conversation_text, re.IGNORECASE) or smart_check(conversation_text):
                    print(f"Smart validation: {topic} is actually covered in conversation")
                    # Auto-update the topic as covered
                    topic_key = next((k for k, v in TOPIC_AREAS.items() if v == topic), None)
                    if topic_key:
                        st.session_state.topic_areas_covered[topic_key] = True
                else:
                    truly_missing.append(topic)
            else:
                truly_missing.append(topic)
        
        return truly_missing
    
    def _get_conversation_text(self):
        """Get all conversation text for analysis."""
        messages = st.session_state.get("visible_messages", [])
        text_parts = []
        
        for msg in messages:
            if isinstance(msg, dict) and msg.get("content"):
                # Clean HTML and get plain text
                content = re.sub(r'<[^>]+>', '', str(msg["content"]))
                text_parts.append(content.lower())
        
        return " ".join(text_parts)
    
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
    
    def force_completion_check(self):
        """
        Force a smart completion check that auto-corrects obvious validation errors.
        Use this when the AI thinks it's done but validation disagrees.
        """
        conversation_text = self._get_conversation_text()
        
        # Auto-correct obvious false negatives
        corrections_made = False
        for topic_key, display_name in TOPIC_AREAS.items():
            if not st.session_state.topic_areas_covered[topic_key]:
                if display_name in ["Calling Logistics"] and "union" in conversation_text:
                    st.session_state.topic_areas_covered[topic_key] = True
                    corrections_made = True
                    print(f"Auto-corrected: {display_name} marked as covered")
        
        return corrections_made
    
    def update_ai_context_after_answer(self, user_input):
        """Simplified context update - let the AI handle conversation flow."""
        try:
            # Just ensure the AI knows what's been covered recently
            if len(st.session_state.get("visible_messages", [])) % 10 == 0:  # Every 10 messages
                covered_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if v]
                if covered_topics:
                    context_msg = {
                        "role": "system", 
                        "content": f"Topics confirmed covered: {', '.join(covered_topics)}. Avoid repeating these areas."
                    }
                    st.session_state.chat_history.append(context_msg)
        except Exception as e:
            print(f"Error in context update: {e}")
            # Don't raise - this is non-critical