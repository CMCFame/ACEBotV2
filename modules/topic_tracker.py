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
        Process topic update messages from the AI with more validation.
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
            
            # Validate updates before applying them
            validated_updates = self._validate_topic_updates(topic_updates)
            
            # Update the session state with validated updates only
            for topic, status in validated_updates.items():
                if topic in st.session_state.topic_areas_covered:
                    old_status = st.session_state.topic_areas_covered[topic]
                    st.session_state.topic_areas_covered[topic] = status
                    print(f"Updated topic {topic} from {old_status} to {status}")
            
            # After updating topics, check for completion
            self._check_completion_status()
            
            # Check for missing critical questions
            self._check_critical_questions()
            
            return True
        except Exception as e:
            print(f"Error processing topic update: {e}")
            return True  # Still return True to hide the malformed update
    
    def _validate_topic_updates(self, topic_updates):
        """
        Validate topic updates to ensure they're not prematurely marked complete.
        Only mark a topic complete if we have substantial evidence.
        """
        validated = {}
        conversation_text = self._get_conversation_text()
        
        for topic, status in topic_updates.items():
            if not status:  # If marking as incomplete, allow it
                validated[topic] = status
                continue
                
            # For marking as complete, validate we have sufficient coverage
            if self._has_sufficient_coverage(topic, conversation_text):
                validated[topic] = status
            else:
                print(f"Rejecting premature completion of topic {topic}")
                # Keep current status instead of updating
                validated[topic] = st.session_state.topic_areas_covered.get(topic, False)
        
        return validated
    
    def _has_sufficient_coverage(self, topic, conversation_text):
        """
        Check if a topic has sufficient coverage to be marked complete.
        """
        # Define minimum requirements for each topic
        requirements = {
            "basic_info": ["name", "company", ("callout", "situation", "type")],
            "staffing_details": ["employee", "staff", "number", ("role", "classification")],
            "contact_process": ["call first", "contact", "device", "why"],
            "list_management": ["list", ("straight", "skip", "order"), "based on"],
            "insufficient_staffing": ["required number", ("different list", "whole list", "not enough")],
            "calling_logistics": ["simultaneous", ("same time", "call again")],
            "list_changes": ["change", ("over time", "update")],
            "tiebreakers": ["tie", ("overtime", "seniority")],
            "additional_rules": [("email", "text"), ("rule", "prevent", "excuse")]
        }
        
        if topic not in requirements:
            return True  # Unknown topic, allow it
        
        required_terms = requirements[topic]
        found_terms = 0
        
        for term in required_terms:
            if isinstance(term, tuple):
                # OR condition - any of the terms in the tuple
                if any(t in conversation_text for t in term):
                    found_terms += 1
            else:
                # Single term
                if term in conversation_text:
                    found_terms += 1
        
        # Require at least 60% of terms to be present
        coverage_ratio = found_terms / len(required_terms)
        return coverage_ratio >= 0.6
    
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
    
    def _check_completion_status(self):
        """Check if all topics are covered and trigger appropriate actions."""
        # Count covered topics
        covered_count = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        
        print(f"Topic coverage: {covered_count}/{total_topics}")
        
        # Only warn about missing topics if we're at 70%+ completion
        if covered_count >= (total_topics * 0.7):
            missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
            if missing_topics:
                # Add system message to explicitly ask about missing topics
                missing_topics_str = ", ".join([TOPIC_AREAS[t] for t in missing_topics])
                system_message = {
                    "role": "system",
                    "content": f"IMPORTANT: The following topics have not been fully covered yet: {missing_topics_str}. "
                               f"Before concluding the questionnaire, ensure you ask specific questions about these topics. "
                               f"Do not consider the questionnaire complete until ALL topics are thoroughly covered."
                }
                
                # Only add if not already present
                recent_messages = st.session_state.chat_history[-3:] if len(st.session_state.chat_history) >= 3 else st.session_state.chat_history
                if not any("following topics have not been fully covered" in msg.get("content", "") for msg in recent_messages):
                    st.session_state.chat_history.append(system_message)
                    print(f"Added system message about missing topics: {missing_topics_str}")
    
    def _check_critical_questions(self):
        """Check if critical questions for covered topics have been asked."""
        conversation_text = self._get_conversation_text()
        
        # Check each covered topic for its critical questions
        for topic, is_covered in st.session_state.topic_areas_covered.items():
            if is_covered and topic in CRITICAL_QUESTIONS:
                missing_questions = []
                
                for question in CRITICAL_QUESTIONS[topic]:
                    # More flexible matching for critical questions
                    question_words = question.lower().split()
                    # Check if most key words from the question appear in conversation
                    matches = sum(1 for word in question_words if len(word) > 3 and word in conversation_text)
                    
                    if matches < len(question_words) * 0.5:  # Less than 50% of words found
                        missing_questions.append(question)
                
                if missing_questions:
                    # Add a system message to ask these questions
                    question_str = "; ".join(missing_questions[:2])  # Limit to avoid overwhelming
                    system_message = {
                        "role": "system",
                        "content": f"CRITICAL: For the {TOPIC_AREAS[topic]} topic, you must still ask about: {question_str}. "
                                   f"Ask these specific questions before considering this topic complete."
                    }
                    
                    # Only add if not recently added
                    recent_messages = st.session_state.chat_history[-2:] if len(st.session_state.chat_history) >= 2 else st.session_state.chat_history
                    if not any(question_str[:20] in msg.get("content", "") for msg in recent_messages):
                        st.session_state.chat_history.append(system_message)
                        print(f"Added system message about missing critical questions for {topic}")
    
    def check_summary_readiness(self):
        """
        Check if the questionnaire is ready for summary generation.
        More strict validation before allowing summary.
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
        
        # Check minimum number of Q&A pairs
        from modules.summary import SummaryGenerator
        summary_gen = SummaryGenerator()
        qa_pairs = summary_gen._extract_qa_pairs_from_visible_messages()
        
        if len(qa_pairs) < 15:  # Minimum threshold
            return {
                "ready": False,
                "message": f"Only {len(qa_pairs)} questions have been answered. Need more comprehensive coverage before generating summary."
            }
        
        # Check for critical question coverage
        conversation_text = self._get_conversation_text()
        missing_critical = []
        
        for topic, questions in CRITICAL_QUESTIONS.items():
            if st.session_state.topic_areas_covered.get(topic, False):
                for question in questions:
                    question_words = question.lower().split()
                    matches = sum(1 for word in question_words if len(word) > 3 and word in conversation_text)
                    
                    if matches < len(question_words) * 0.4:
                        missing_critical.append(f"{TOPIC_AREAS[topic]}: {question}")
        
        if missing_critical:
            return {
                "ready": False,
                "missing_questions": missing_critical[:5],  # Show first 5
                "message": f"Critical questions still need to be addressed: {'; '.join(missing_critical[:3])}"
            }
        
        # All checks passed
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
    
    def force_topic_reset(self):
        """Force reset of all topics to incomplete - for debugging."""
        for topic in st.session_state.topic_areas_covered:
            st.session_state.topic_areas_covered[topic] = False
        print("All topics reset to incomplete")
    
    def manual_topic_update(self, topic_updates):
        """Manually update topic coverage - for debugging."""
        for topic, status in topic_updates.items():
            if topic in st.session_state.topic_areas_covered:
                st.session_state.topic_areas_covered[topic] = status
                print(f"Manually updated {topic} to {status}")
    
    def update_ai_context_after_answer(self, user_input):
        """Update AI context after each user answer to prevent circular questioning."""
        try:
            # Ensure required session state exists
            if not hasattr(st.session_state, 'visible_messages') or not hasattr(st.session_state, 'chat_history'):
                print("Warning: Session state not fully initialized for context update")
                return
                
            visible_messages = st.session_state.get("visible_messages", [])
            
            # Analyze the last few messages to determine what question was just answered
            if len(visible_messages) >= 2:
                last_msg = visible_messages[-1]  # User's answer
                prev_msg = visible_messages[-2]  # Assistant's question
                
                if last_msg.get("role") == "user" and prev_msg.get("role") == "assistant":
                    # Check if this is a substantive answer (not just asking for an example)
                    user_content = last_msg.get("content", "").lower().strip()
                    if user_content not in ["example", "can you show me an example?", "show example"]:
                        # Extract the question from the assistant's message
                        prev_content = prev_msg.get("content", "")
                        question_asked = ""
                        for sentence in prev_content.split(". "):
                            if "?" in sentence:
                                question_asked = sentence.strip() + "?"
                                break
                        
                        if question_asked:
                            # Check which of our original questions this might be
                            matched_questions = []
                            questions_list = st.session_state.get("questions", [])
                            for i, q in enumerate(questions_list):
                                # Simple word overlap check
                                q_words = set(q.lower().split())
                                asked_words = set(question_asked.lower().split())
                                if len(q_words.intersection(asked_words)) / max(len(q_words), 1) > 0.3:
                                    matched_questions.append(i)
                            
                            # Add context message to avoid asking this question again
                            if matched_questions:
                                question_info = ", ".join([f"question {i+1}" for i in matched_questions])
                                context_msg = {
                                    "role": "system",
                                    "content": f"The user has just answered {question_info} with: '{last_msg.get('content', '')}'. Do not ask this question again."
                                }
                                st.session_state.chat_history.append(context_msg)
                                
                                # Also check if this completes a topic
                                self._update_topic_coverage_from_answer(question_asked, last_msg.get("content", ""))
        except Exception as e:
            print(f"Error in update_ai_context_after_answer: {e}")
            # Don't raise the exception, just log it and continue
    
    def _update_topic_coverage_from_answer(self, question, answer):
        """Update topic coverage based on answers to key questions."""
        try:
            combined_text = (str(question) + " " + str(answer)).lower()
            
            # Map of key phrases to topics they complete
            completion_phrases = {
                "contact first": "contact_process",
                "devices have": "contact_process", 
                "call straight down": "list_management",
                "skip those who are on": "list_management",
                "call neighboring district": "insufficient_staffing",
                "call all devices simultaneously": "calling_logistics",
                "lists update": "list_changes",
                "seniority is used as": "tiebreakers",
                "hours of rest": "additional_rules"
            }
            
            # Check for completion phrases
            for phrase, topic in completion_phrases.items():
                if phrase in combined_text:
                    topic_areas_covered = st.session_state.get("topic_areas_covered", {})
                    if topic in topic_areas_covered:
                        st.session_state.topic_areas_covered[topic] = True
                        print(f"Auto-updated topic {topic} to True based on answer pattern")
        except Exception as e:
            print(f"Error in _update_topic_coverage_from_answer: {e}")