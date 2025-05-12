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
        
        # Get answered questions count
        from modules.summary import SummaryGenerator
        summary_gen = SummaryGenerator()
        responses = summary_gen.get_responses_as_list()
        
        # Check if at least 70% of questions have been answered
        answered_count = len(responses)
        total_questions = len(st.session_state.questions)
        
        if answered_count / total_questions < 0.7:
            missing_count = total_questions - answered_count
            return {
                "ready": False,
                "missing_questions": [f"{missing_count} questions still unanswered"],
                "message": f"Please continue answering questions. There are still approximately {missing_count} questions that need answers."
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
        
    def verify_question_coverage(self):
        """Verify which specific questions have been answered."""
        # Get all responses from the summary generator
        from modules.summary import SummaryGenerator
        summary_gen = SummaryGenerator()
        responses = summary_gen.get_responses_as_list()
        conversation_insights = summary_gen._extract_insights_from_conversation()
        
        # Create a mapping of questions to answers
        question_answer_map = {}
        
        # Add explicitly tracked responses
        for question, answer in responses:
            clean_question = summary_gen._normalize_question(question)
            question_answer_map[clean_question] = answer
        
        # Add conversation insights
        for question, answer in conversation_insights.items():
            if question not in question_answer_map:
                question_answer_map[question] = answer
        
        # Count answered questions for each topic
        topic_question_coverage = {topic: 0 for topic in TOPIC_AREAS.keys()}
        topic_question_total = {topic: 0 for topic in TOPIC_AREAS.keys()}
        
        # Map questions to topics
        question_to_topic = {
            "name and company": "basic_info",
            "situation": "basic_info",
            "employees required": "staffing_details",
            "roles": "staffing_details",
            "call first": "contact_process",
            "devices": "contact_process",
            "device first": "contact_process",
            "same list": "list_management",
            "lists total": "list_management",
            "job classification": "list_management",
            "call this list": "list_management",
            "straight down": "list_management",
            "skip around": "list_management",
            "pauses": "list_management",
            "required number": "insufficient_staffing",
            "different list": "insufficient_staffing",
            "different location": "insufficient_staffing",
            "offer position": "insufficient_staffing",
            "whole list again": "insufficient_staffing",
            "do differently": "insufficient_staffing",
            "simultaneously": "calling_logistics",
            "no but call again": "calling_logistics",
            "first pass": "calling_logistics",
            "change over time": "list_changes",
            "when change": "list_changes",
            "content change": "list_changes",
            "tie breakers": "tiebreakers",
            "email or text": "additional_rules",
            "prevent called": "additional_rules",
            "excuse declined": "additional_rules",
        }
        
        # Count questions by topic
        for question in st.session_state.questions:
            normalized = summary_gen._normalize_question(question)
            topic = None
            
            # Find matching topic
            for key, topic_name in question_to_topic.items():
                if key in normalized:
                    topic = topic_name
                    break
            
            if topic:
                topic_question_total[topic] += 1
                if normalized in question_answer_map:
                    topic_question_coverage[topic] += 1
        
        # Calculate coverage percentages
        coverage_results = {}
        for topic, covered in topic_question_coverage.items():
            total = topic_question_total[topic] or 1  # Avoid division by zero
            coverage_results[topic] = {
                "covered": covered,
                "total": total,
                "percentage": int((covered / total) * 100)
            }
        
        return coverage_results
        
    def update_ai_context_after_answer(self, user_input):
        """Update AI context after each user answer to prevent circular questioning."""
        # Analyze the last few messages to determine what question was just answered
        if len(st.session_state.visible_messages) >= 2:
            last_msg = st.session_state.visible_messages[-1]  # User's answer
            prev_msg = st.session_state.visible_messages[-2]  # Assistant's question
            
            if last_msg["role"] == "user" and prev_msg["role"] == "assistant":
                # Check if this is a substantive answer (not just asking for an example)
                if last_msg["content"].lower().strip() not in ["example", "can you show me an example?", "show example"]:
                    # Extract the question from the assistant's message
                    question_asked = ""
                    for sentence in prev_msg["content"].split(". "):
                        if "?" in sentence:
                            question_asked = sentence.strip() + "?"
                            break
                    
                    if question_asked:
                        # Check which of our original questions this might be
                        matched_questions = []
                        for i, q in enumerate(st.session_state.questions):
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
                                "content": f"The user has just answered {question_info} with: '{last_msg['content']}'. Do not ask this question again."
                            }
                            st.session_state.chat_history.append(context_msg)
                            
                            # Also check if this completes a topic
                            self._update_topic_coverage_from_answer(question_asked, last_msg["content"])
    
    def _update_topic_coverage_from_answer(self, question, answer):
        """Update topic coverage based on answers to key questions."""
        combined_text = (question + " " + answer).lower()
        
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
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = True