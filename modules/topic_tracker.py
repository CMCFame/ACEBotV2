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
        
        # Add loop detection (NEW)
        if 'conversation_loop_detector' not in st.session_state:
            st.session_state.conversation_loop_detector = []
        
        # Add answered questions tracking for better completion detection (NEW)
        if 'answered_questions' not in st.session_state:
            st.session_state.answered_questions = set()
            
        # Add example tracking to prevent loops (NEW)
        if 'last_example_question' not in st.session_state:
            st.session_state.last_example_question = None
    
    # NEW: Loop detection functionality
    def detect_conversation_loop(self, user_input, last_ai_response):
        """Detect if we're in a conversation loop."""
        # Clean inputs for comparison
        user_clean = user_input.lower().strip()
        ai_clean = last_ai_response.lower().strip()[:200]  # First 200 chars
        
        current_exchange = (user_clean, ai_clean)
        st.session_state.conversation_loop_detector.append(current_exchange)
        
        # Keep only last 8 exchanges
        if len(st.session_state.conversation_loop_detector) > 8:
            st.session_state.conversation_loop_detector.pop(0)
        
        # Check for loops - if last 3 exchanges are very similar
        if len(st.session_state.conversation_loop_detector) >= 3:
            recent_exchanges = st.session_state.conversation_loop_detector[-3:]
            
            # Check for example loop specifically
            example_requests = ["example", "show example", "can you show me an example"]
            if all(any(req in ex[0] for req in example_requests) for ex in recent_exchanges):
                return True
                
            # Check for identical exchanges
            if all(ex == recent_exchanges[0] for ex in recent_exchanges):
                return True
        
        return False
    
    # NEW: Force progression when stuck in loop
    def break_loop_with_next_question(self):
        """Force progression to next unanswered question."""
        # Find next critical question that hasn't been answered
        questions = st.session_state.get("questions", [])
        current_idx = st.session_state.get("current_question_index", 0)
        
        # Try to advance to next question
        if current_idx + 1 < len(questions):
            next_question = questions[current_idx + 1]
            st.session_state.current_question_index = current_idx + 1
            st.session_state.current_question = next_question
            return f"I notice we may be repeating ourselves. Let's move forward with the next question:\n\n{next_question}"
        
        # If we're near the end, check what's still missing
        return self._force_topic_completion_check()
    
    # NEW: Enhanced force completion check
    def _force_topic_completion_check(self):
        """Force a completion check when we might be done."""
        missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
        
        if not missing_topics:
            return "Excellent! It looks like we've covered all the essential topics comprehensively. Let me prepare your summary."
        else:
            # Pick the most important missing topic
            priority_topics = ["contact_process", "list_management", "insufficient_staffing"]
            next_topic = None
            
            for priority in priority_topics:
                if not st.session_state.topic_areas_covered.get(priority, False):
                    next_topic = TOPIC_AREAS.get(priority)
                    break
            
            if not next_topic and missing_topics:
                next_topic = missing_topics[0]
            
            return f"We still need to cover some important areas. Let me ask you about {next_topic}."
    
    # NEW: Mark individual questions as answered
    def mark_question_answered(self, question_index, user_response):
        """Mark a specific question as answered."""
        if len(user_response.strip()) > 10:  # Substantial response
            st.session_state.answered_questions.add(question_index)
    
    # ORIGINAL: Process topic update messages from the AI with improved validation
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
            
            # Validate updates before applying them - ENHANCED
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
    
    # ORIGINAL but ENHANCED: Validate topic updates with more lenient criteria
    def _validate_topic_updates(self, topic_updates):
        """
        Validate topic updates to ensure they're not prematurely marked complete.
        Enhanced to be more lenient while still maintaining quality.
        """
        validated = {}
        conversation_text = self._get_conversation_text()
        
        for topic, status in topic_updates.items():
            if not status:  # If marking as incomplete, allow it
                validated[topic] = status
                continue
                
            # For marking as complete, use enhanced validation
            if self._has_sufficient_coverage(topic, conversation_text):
                validated[topic] = status
            else:
                print(f"Rejecting premature completion of topic {topic}")
                # Keep current status instead of updating
                validated[topic] = st.session_state.topic_areas_covered.get(topic, False)
        
        return validated
    
    # ENHANCED: More lenient but still thorough coverage check
    def _has_sufficient_coverage(self, topic, conversation_text):
        """
        Check if a topic has sufficient coverage to be marked complete.
        Enhanced to be more lenient while maintaining quality.
        """
        # Define minimum requirements for each topic - ENHANCED
        requirements = {
            "basic_info": [
                ["name", "company"], 
                ["callout", "situation", "type", "outage", "emergency"]
            ],
            "staffing_details": [
                ["employee", "staff", "people", "person"], 
                ["number", "how many", "required", "need"]
            ],
            "contact_process": [
                ["call", "contact", "reach", "phone"], 
                ["first", "who", "initially"],
                ["device", "phone", "cell", "mobile"]
            ],
            "list_management": [
                ["list", "group", "roster"], 
                ["order", "sequence", "how", "method"],
                ["based on", "organized", "sorted"]
            ],
            "insufficient_staffing": [
                ["not enough", "insufficient", "short", "can't get"], 
                ["different list", "whole list", "again", "other"]
            ],
            "calling_logistics": [
                ["simultaneous", "same time", "together", "all at once"],
                ["call again", "second pass", "retry"]
            ],
            "list_changes": [
                ["change", "update", "modify", "alter"], 
                ["over time", "when", "how often"]
            ],
            "tiebreakers": [
                ["tie", "equal", "same"], 
                ["overtime", "seniority", "hours", "experience"]
            ],
            "additional_rules": [
                ["rule", "policy", "regulation"], 
                ["email", "text", "message", "notification"],
                ["shift", "work", "schedule", "excuse"]
            ]
        }
        
        if topic not in requirements:
            return True  # Unknown topic, allow it
        
        topic_requirements = requirements[topic]
        groups_satisfied = 0
        
        # Check each group of requirements
        for requirement_group in topic_requirements:
            group_satisfied = False
            for term in requirement_group:
                if term.lower() in conversation_text.lower():
                    group_satisfied = True
                    break
            if group_satisfied:
                groups_satisfied += 1
        
        # Need at least 60% of requirement groups satisfied
        coverage_ratio = groups_satisfied / len(topic_requirements)
        is_sufficient = coverage_ratio >= 0.6
        
        # ENHANCED: Also check individual question tracking
        answered_count = len(st.session_state.answered_questions)
        questions_count = len(st.session_state.get("questions", []))
        
        if answered_count >= questions_count * 0.5:  # If 50%+ questions answered
            return True  # Be more lenient
            
        return is_sufficient
    
    # ORIGINAL: Get conversation text for analysis
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
    
    # ENHANCED: Check completion status with dual criteria
    def _check_completion_status(self):
        """Check if all topics are covered and trigger appropriate actions."""
        # Count covered topics
        covered_count = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        
        # Also consider individual questions
        answered_count = len(st.session_state.answered_questions)
        questions_count = len(st.session_state.get("questions", []))
        
        print(f"Topic coverage: {covered_count}/{total_topics}")
        print(f"Question coverage: {answered_count}/{questions_count}")
        
        # Enhanced completion criteria
        topic_pct = covered_count / total_topics
        question_pct = answered_count / max(questions_count, 1)
        
        # Only warn about missing topics if we're at 70%+ completion OR 60%+ questions answered
        if topic_pct >= 0.7 or question_pct >= 0.6:
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
    
    # ORIGINAL: Check critical questions for covered topics
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
                    
                    if matches < len(question_words) * 0.4:  # Less than 40% of words found
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
    
    # ENHANCED: More lenient summary readiness check
    def check_summary_readiness(self):
        """
        Check if the questionnaire is ready for summary generation.
        Enhanced with dual criteria and more lenient validation.
        """
        # Check if all topics are covered
        covered_count = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        
        # Check individual questions
        answered_count = len(st.session_state.answered_questions)
        questions_count = len(st.session_state.get("questions", []))
        
        topic_pct = covered_count / total_topics
        question_pct = answered_count / max(questions_count, 1)
        
        # Enhanced completion criteria - multiple ways to be "ready"
        if topic_pct >= 1.0:  # All topics covered
            return {
                "ready": True,
                "message": f"Perfect! All {total_topics} topic areas have been covered comprehensively."
            }
        
        if topic_pct >= 0.8 and question_pct >= 0.6:  # 80% topics + 60% questions
            return {
                "ready": True,
                "message": f"Great progress! You've covered {covered_count}/{total_topics} topic areas and answered {answered_count} questions."
            }
            
        if question_pct >= 0.8:  # 80% of individual questions answered
            return {
                "ready": True,
                "message": f"Excellent! You've answered {answered_count}/{questions_count} questions comprehensively."
            }
        
        # Not ready yet
        missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
        
        if not missing_topics:
            return {
                "ready": False,
                "message": f"Only {len(self._extract_qa_pairs_from_conversation())} questions have been answered. Need more comprehensive coverage before generating summary."
            }
        
        return {
            "ready": False,
            "missing_topics": missing_topics[:3],  # Show max 3
            "message": f"We still need to cover: {', '.join(missing_topics[:3])}"
        }
    
    # HELPER: Extract Q&A pairs from conversation
    def _extract_qa_pairs_from_conversation(self):
        """Extract question-answer pairs from the conversation."""
        qa_pairs = []
        visible_messages = st.session_state.get("visible_messages", [])
        
        i = 0
        while i < len(visible_messages) - 1:
            current_msg = visible_messages[i]
            next_msg = visible_messages[i + 1]
            
            if (current_msg.get("role") == "assistant" and 
                next_msg.get("role") == "user" and
                "?" in current_msg.get("content", "")):
                
                question = current_msg.get("content", "")
                answer = next_msg.get("content", "")
                
                # Clean the question
                if "?" in question:
                    question = question.split("?")[0] + "?"
                
                # Skip very short answers or command-like responses
                if len(answer.split()) >= 3:
                    qa_pairs.append((question, answer))
            
            i += 1
        
        return qa_pairs
    
    # ORIGINAL: Calculate progress percentage with enhancement
    def get_progress_percentage(self):
        """Calculate the current progress percentage based on topic coverage and questions."""
        topic_progress = sum(st.session_state.topic_areas_covered.values()) / len(st.session_state.topic_areas_covered)
        
        # Also factor in individual question progress
        answered_count = len(st.session_state.answered_questions)
        questions_count = len(st.session_state.get("questions", []))
        question_progress = answered_count / max(questions_count, 1)
        
        # Use weighted average: 70% topics, 30% individual questions
        combined_progress = (topic_progress * 0.7) + (question_progress * 0.3)
        return int(combined_progress * 100)
    
    # ENHANCED: Get detailed progress data for UI display
    def get_progress_data(self):
        """Get detailed progress data for UI display."""
        covered_topics = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        answered_count = len(st.session_state.answered_questions)
        
        return {
            "percentage": self.get_progress_percentage(),
            "covered_count": covered_topics,
            "total_count": total_topics,
            "covered_topics": [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if v],
            "missing_topics": [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v],
            "questions_answered": answered_count,
            "total_questions": len(st.session_state.get("questions", [])),
            "loop_detections": len(st.session_state.get("conversation_loop_detector", []))
        }
    
    # ORIGINAL: Force reset for debugging
    def force_topic_reset(self):
        """Force reset of all topics to incomplete - for debugging."""
        for topic in st.session_state.topic_areas_covered:
            st.session_state.topic_areas_covered[topic] = False
        print("All topics reset to incomplete")
    
    # ORIGINAL: Manual topic update for debugging
    def manual_topic_update(self, topic_updates):
        """Manually update topic coverage - for debugging."""
        for topic, status in topic_updates.items():
            if topic in st.session_state.topic_areas_covered:
                st.session_state.topic_areas_covered[topic] = status
                print(f"Manually updated {topic} to {status}")
    
    # ENHANCED: Update AI context after each user answer
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
                                
                                # Mark questions as answered
                                for q_idx in matched_questions:
                                    self.mark_question_answered(q_idx, user_input)
                                
                                # Also check if this completes a topic
                                self._update_topic_coverage_from_answer(question_asked, last_msg.get("content", ""))
        except Exception as e:
            print(f"Error in update_ai_context_after_answer: {e}")
            # Don't raise the exception, just log it and continue
    
    # ENHANCED: Update topic coverage from answers
    def _update_topic_coverage_from_answer(self, question, answer):
        """Update topic coverage based on answers to key questions."""
        try:
            combined_text = (str(question) + " " + str(answer)).lower()
            
            # Enhanced map of key phrases to topics they complete
            completion_phrases = {
                # Basic info
                "name": "basic_info",
                "company": "basic_info",
                "callout": "basic_info",
                "situation": "basic_info",
                
                # Staffing
                "employees": "staffing_details",
                "how many": "staffing_details",
                "staff": "staffing_details",
                "roles": "staffing_details",
                
                # Contact process
                "call first": "contact_process",
                "contact first": "contact_process",
                "devices": "contact_process",
                "phone": "contact_process",
                
                # List management
                "straight down": "list_management",
                "skip": "list_management",
                "list": "list_management",
                "order": "list_management",
                
                # Insufficient staffing
                "required number": "insufficient_staffing",
                "not enough": "insufficient_staffing",
                "different list": "insufficient_staffing",
                "whole list": "insufficient_staffing",
                
                # Calling logistics
                "simultaneous": "calling_logistics",
                "same time": "calling_logistics",
                "call again": "calling_logistics",
                
                # List changes
                "change": "list_changes",
                "update": "list_changes",
                "over time": "list_changes",
                
                # Tiebreakers
                "tie": "tiebreakers",
                "overtime": "tiebreakers",
                "seniority": "tiebreakers",
                
                # Additional rules
                "email": "additional_rules",
                "text": "additional_rules",
                "rule": "additional_rules",
                "shift": "additional_rules"
            }
            
            # Check for completion phrases
            for phrase, topic in completion_phrases.items():
                if phrase in combined_text:
                    topic_areas_covered = st.session_state.get("topic_areas_covered", {})
                    if topic in topic_areas_covered and not topic_areas_covered[topic]:
                        # Only auto-complete if there's substantial content
                        if len(answer.split()) >= 5:
                            st.session_state.topic_areas_covered[topic] = True
                            print(f"Auto-updated topic {topic} to True based on answer pattern: {phrase}")
                            break  # Only update one topic per answer
                            
        except Exception as e:
            print(f"Error in _update_topic_coverage_from_answer: {e}")
    
    # NEW: Check if we should force progression
    def should_force_progression(self):
        """Check if we should force progression to avoid loops."""
        current_idx = st.session_state.get("current_question_index", 0)
        questions_count = len(st.session_state.get("questions", []))
        
        # If we're stuck on the same question for too long
        loop_entries = len(st.session_state.conversation_loop_detector)
        if loop_entries >= 6:  # Too many recent exchanges
            return True
            
        # If we have good coverage but haven't progressed
        answered_count = len(st.session_state.answered_questions)
        if answered_count >= current_idx + 3:  # Answered more than current position suggests
            return True
            
        return False