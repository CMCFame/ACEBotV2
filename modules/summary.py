# modules/summary.py
import streamlit as st
from datetime import datetime
from collections import OrderedDict
from config import TOPIC_AREAS

class SummaryGenerator:
    def __init__(self):
        """Initialize the summary generator."""
        pass
    
    def generate_conversation_summary(self):
        """Generate a comprehensive summary of the conversation."""
        # Extract all question-answer pairs from the conversation
        summary_pairs = []
        current_question = ""
        
        # Process conversation in order
        for i in range(len(st.session_state.visible_messages)):
            message = st.session_state.visible_messages[i]
            
            # Identify questions from the assistant (excluding examples)
            if message["role"] == "assistant" and "?" in message["content"]:
                question_content = message["content"]
                
                # Skip example text when identifying the question
                if "*Example:" in question_content:
                    parts = question_content.split("*Example:")
                    if len(parts) > 1 and "?" in parts[1]:
                        # Look for the real question after the example
                        lines = parts[1].split("\n")
                        for line in lines:
                            if "?" in line and not line.startswith("*Example:"):
                                current_question = line.strip()
                                break
                else:
                    # Extract the question - look for the last sentence with a question mark
                    sentences = question_content.split(". ")
                    for sentence in reversed(sentences):
                        if "?" in sentence:
                            current_question = sentence.strip()
                            break
            
            # If user message follows a question, it's likely an answer (except examples)
            elif message["role"] == "user" and current_question and i > 0:
                # Skip if this is just an example request
                if message["content"].lower().strip() in ["example", "can you show me an example?", "show example"]:
                    continue
                    
                # This is an actual answer - add it to our pairs
                summary_pairs.append((current_question, message["content"]))
                current_question = ""  # Reset current question
        
        # Format the summary as a string
        summary = "# ACE Questionnaire Summary\n\n"
        summary += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if st.session_state.user_info["name"] or st.session_state.user_info["company"]:
            summary += f"## User Information\n"
            if st.session_state.user_info["name"]:
                summary += f"Name: {st.session_state.user_info['name']}\n"
            if st.session_state.user_info["company"]:
                summary += f"Company: {st.session_state.user_info['company']}\n"
            summary += "\n"
        
        summary += "## Questionnaire Responses\n\n"
        
        # Enhanced categorization for more accurate topic mapping
        enhanced_topic_mapping = {
            # Basic Information
            "name": "Basic Information",
            "company": "Basic Information",
            "situation": "Basic Information", 
            "frequent": "Basic Information",
            "callout type": "Basic Information",
            "callout occur": "Basic Information",
            
            # Staffing Details
            "employee": "Staffing Details",
            "staff": "Staffing Details",
            "role": "Staffing Details",
            "classification": "Staffing Details",
            "journeymen": "Staffing Details",
            "apprentice": "Staffing Details",
            "supervisor": "Staffing Details",
            
            # Contact Process
            "contact first": "Contact Process",
            "contact when": "Contact Process",
            "who do you contact": "Contact Process",
            "device": "Contact Process",
            "phone": "Contact Process",
            "call first": "Contact Process",
            "why are they contacted": "Contact Process",
            
            # List Management
            "list": "List Management",
            "skip": "List Management",
            "traverse": "List Management",
            "straight down": "List Management",
            "order": "List Management",
            "pause": "List Management",
            "organized": "List Management",
            
            # Insufficient Staffing
            "required number": "Insufficient Staffing",
            "don't get": "Insufficient Staffing",
            "not enough": "Insufficient Staffing",
            "secondary list": "Insufficient Staffing",
            "part-time": "Insufficient Staffing",
            "whole list again": "Insufficient Staffing",
            "can't get enough": "Insufficient Staffing",
            "neighboring district": "Insufficient Staffing",
            "contractor": "Insufficient Staffing",
            "short-staffed": "Insufficient Staffing",
            
            # Calling Logistics
            "simultaneous": "Calling Logistics",
            "call again": "Calling Logistics",
            "second pass": "Calling Logistics",
            "nobody else accepts": "Calling Logistics",
            "all device": "Calling Logistics",
            "ensure quick response": "Calling Logistics",
            
            # List Changes
            "change": "List Changes",
            "update": "List Changes",
            "overtime hours": "List Changes",
            "new hire": "List Changes",
            "transfer": "List Changes",
            "content of the list": "List Changes",
            "pay period": "List Changes",
            
            # Tiebreakers
            "tie": "Tiebreakers",
            "tiebreaker": "Tiebreakers",
            "seniority": "Tiebreakers",
            "alphabetical": "Tiebreakers",
            "rotating": "Tiebreakers",
            
            # Additional Rules
            "text alert": "Additional Rules",
            "email": "Additional Rules",
            "rule": "Additional Rules",
            "shift": "Additional Rules",
            "exempt": "Additional Rules",
            "rest": "Additional Rules",
            "hour": "Additional Rules",
            "excuse": "Additional Rules",
            "declined callout": "Additional Rules"
        }
        
        # Define the preferred order of topics
        topic_order = [
            "Basic Information", 
            "Staffing Details", 
            "Contact Process", 
            "List Management", 
            "Insufficient Staffing", 
            "Calling Logistics",
            "List Changes", 
            "Tiebreakers", 
            "Additional Rules"
        ]
        
        # Initialize ordered dict with empty lists for each topic
        topic_buckets = OrderedDict()
        for topic in topic_order:
            topic_buckets[topic] = []
        
        # Add "Other" for anything that doesn't match
        topic_buckets["Other"] = []
        
        # Improved categorization algorithm
        for question, answer in summary_pairs:
            topic_assigned = False
            best_match_topic = None
            max_matches = 0
            
            # Combine question and answer text for better matching
            combined_text = (question + " " + answer).lower()
            
            # Count matches for each topic's keywords
            for topic in topic_order:
                keyword_matches = 0
                topic_keywords = [kw for kw, t in enhanced_topic_mapping.items() if t == topic]
                
                for keyword in topic_keywords:
                    if keyword.lower() in combined_text:
                        keyword_matches += 1
                
                # Track the topic with the most keyword matches
                if keyword_matches > max_matches:
                    max_matches = keyword_matches
                    best_match_topic = topic
            
            # Assign to best matching topic if we found any matches
            if max_matches > 0:
                topic_buckets[best_match_topic].append((question, answer))
                topic_assigned = True
            
            # If no match found, assign to "Other"
            if not topic_assigned:
                topic_buckets["Other"].append((question, answer))
        
        # Add topics to summary
        for topic, qa_pairs in topic_buckets.items():
            if qa_pairs:  # Only include topics that have QA pairs
                summary += f"### {topic}\n\n"
                for question, answer in qa_pairs:
                    summary += f"**Q: {question}**\n\n"
                    summary += f"A: {answer}\n\n"
        
        return summary
    
    def get_responses_as_list(self):
        """Extract responses as list of (question, answer) tuples for exports."""
        # This returns a clean list of all user responses
        responses = []
        
        # First use explicit responses list
        if hasattr(st.session_state, 'responses') and st.session_state.responses:
            responses.extend(st.session_state.responses)
        
        # Then supplement with additional extracted responses from visible messages
        current_question = ""
        
        for i in range(len(st.session_state.visible_messages)):
            message = st.session_state.visible_messages[i]
            
            # Identify questions from the assistant (excluding examples)
            if message["role"] == "assistant" and "?" in message["content"]:
                question_content = message["content"]
                
                # Skip example text when identifying the question
                if "*Example:" in question_content:
                    parts = question_content.split("*Example:")
                    if len(parts) > 1 and "?" in parts[1]:
                        # Look for the real question after the example
                        lines = parts[1].split("\n")
                        for line in lines:
                            if "?" in line and not line.startswith("*Example:"):
                                current_question = line.strip()
                                break
                else:
                    # Extract the question - look for the last sentence with a question mark
                    sentences = question_content.split(". ")
                    for sentence in reversed(sentences):
                        if "?" in sentence:
                            current_question = sentence.strip()
                            break
            
            # If user message follows a question, it's likely an answer (except examples)
            elif message["role"] == "user" and current_question and i > 0:
                # Skip if this is just an example request
                if message["content"].lower().strip() in ["example", "can you show me an example?", "show example"]:
                    continue
                
                # Check if this pair is already in responses
                pair = (current_question, message["content"])
                if pair not in responses:
                    responses.append(pair)
                    
                current_question = ""  # Reset current question
        
        return responses
    
    def generate_progress_dashboard(self):
        """Generate a comprehensive dashboard of all questions and answers."""
        # Get all responses from explicit list
        responses = self.get_responses_as_list()
        
        # Extract additional insights from conversation
        conversation_insights = self._extract_insights_from_conversation()
        
        # Create a mapping of questions to answers
        question_answer_map = {}
        
        # First add explicitly tracked responses
        for question, answer in responses:
            # Clean up question to match original question list
            clean_question = self._normalize_question(question)
            question_answer_map[clean_question] = answer
        
        # Then add conversation insights (these are inferred matches)
        for question, answer in conversation_insights.items():
            if question not in question_answer_map:
                question_answer_map[question] = answer
        
        # Format as markdown dashboard
        dashboard = "# ACE Questionnaire Progress\n\n"
        dashboard += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        if st.session_state.user_info["name"] or st.session_state.user_info["company"]:
            dashboard += f"## User Information\n"
            if st.session_state.user_info["name"]:
                dashboard += f"**Name:** {st.session_state.user_info['name']}\n"
            if st.session_state.user_info["company"]:
                dashboard += f"**Company:** {st.session_state.user_info['company']}\n"
            dashboard += "\n"
        
        # Show progress by topic
        dashboard += "## Progress by Topic\n\n"
        
        for topic, display_name in TOPIC_AREAS.items():
            is_covered = st.session_state.topic_areas_covered.get(topic, False)
            status = "✅ Completed" if is_covered else "❌ Not Covered"
            dashboard += f"**{display_name}**: {status}\n"
        
        dashboard += "\n## All Questions and Answers\n\n"
        
        # Calculate answers found
        answers_found = sum(1 for q in st.session_state.questions if self._normalize_question(q) in question_answer_map)
        dashboard += f"**Questions Answered:** {answers_found} of {len(st.session_state.questions)}\n\n"
        
        # Add all questions and answers
        for i, question in enumerate(st.session_state.questions):
            normalized_q = self._normalize_question(question)
            if normalized_q in question_answer_map:
                dashboard += f"### Q{i+1}: {question}\n\n"
                dashboard += f"{question_answer_map[normalized_q]}\n\n"
            else:
                dashboard += f"### Q{i+1}: {question}\n\n"
                dashboard += f"*No answer provided yet*\n\n"
        
        return dashboard

    # In modules/summary.py - Replace the _extract_insights_from_conversation method

    def _extract_insights_from_conversation(self):
        """Extract detailed insights from the conversation to map to specific questions."""
        # Create a mapping of questions to answers
        insights = {}
        
        # This dictionary maps keywords to specific question numbers in questions.txt
        keyword_to_question = {
            # Basic Info
            "name and company": 1,
            "situation": 2,
            # Staffing
            "employees required": 3,
            # Contact Process
            "call first": 4,
            "why": 5,
            "devices have": 6,
            "device first": 7,
            "type of devices": 8,
            # List Management
            "same list": 9,
            "lists total": 10, 
            "job classification": 11,
            "other attribute": 12,
            "how do you call": 13,
            "straight down": 14,
            "skip around": [15, 16, 17, 18],
            "pauses": 19,
            # Insufficient Staffing
            "don't get required": 20,
            "different list": 21,
            "different location": 22,
            "offer position": 23,
            "consider list again": 24,
            "call list again": 25,
            "do differently": 26,
            # Calling Logistics
            "calling simultaneously": [27, 28],
            "call again if nobody": 29,
            "first pass": 30,
            # List Changes
            "change over time": 31,
            "when change": 32,
            "order change": 33,
            "content change": 34,
            "when content change": 35,
            "how content change": 36,
            # Tiebreakers
            "tie breakers": 37,
            "first tiebreaker": 38,
            "second tiebreaker": 39,
            "third tiebreaker": 40,
            # Additional Rules
            "email or text": 41,
            "rules prevent": 42,
            "rules excuse": 43
        }
        
        # Get conversation pairs (assistant question followed by user answer)
        conversation_pairs = []
        for i in range(len(st.session_state.visible_messages) - 1):
            if (st.session_state.visible_messages[i]["role"] == "assistant" and 
                st.session_state.visible_messages[i+1]["role"] == "user"):
                
                asst_msg = st.session_state.visible_messages[i]["content"]
                user_msg = st.session_state.visible_messages[i+1]["content"]
                
                # Skip example requests
                if user_msg.lower().strip() in ["example", "can you show me an example?", "show example"]:
                    continue
                    
                conversation_pairs.append((asst_msg, user_msg))
        
        # Process each conversation pair
        for asst_msg, user_msg in conversation_pairs:
            # Process only substantive user answers (not just requests for examples)
            if len(user_msg) > 10:
                # Find which question this answer corresponds to
                for keyword, question_numbers in keyword_to_question.items():
                    if keyword.lower() in asst_msg.lower():
                        # Handle single question number or list of question numbers
                        if isinstance(question_numbers, list):
                            for q_num in question_numbers:
                                if q_num <= len(st.session_state.questions):
                                    question = st.session_state.questions[q_num-1]
                                    insights[self._normalize_question(question)] = user_msg
                        else:
                            if question_numbers <= len(st.session_state.questions):
                                question = st.session_state.questions[question_numbers-1]
                                insights[self._normalize_question(question)] = user_msg
        
        # For better question matching, also use the raw Q&A pairs from the conversation
        assistant_questions = []
        for i, msg in enumerate(st.session_state.visible_messages):
            if msg["role"] == "assistant" and "?" in msg["content"]:
                last_question_part = ""
                # Find the last question in the message
                for sentence in msg["content"].split(". "):
                    if "?" in sentence:
                        last_question_part = sentence.strip() + "?"
                
                if last_question_part and i+1 < len(st.session_state.visible_messages):
                    if st.session_state.visible_messages[i+1]["role"] == "user":
                        user_response = st.session_state.visible_messages[i+1]["content"]
                        if user_response.lower().strip() not in ["example", "can you show me an example?", "show example"]:
                            assistant_questions.append((last_question_part, user_response))
        
        # Match these questions to the original questions list
        for asst_q, user_answer in assistant_questions:
            best_match = None
            best_score = 0
            
            for i, q in enumerate(st.session_state.questions):
                # Calculate similarity score based on word overlap
                q_words = set(q.lower().split())
                asst_words = set(asst_q.lower().split())
                intersection = q_words.intersection(asst_words)
                
                # Calculate score based on word overlap ratio
                if len(q_words) > 0:
                    score = len(intersection) / len(q_words)
                    if score > best_score and score > 0.3:  # 30% word overlap threshold
                        best_score = score
                        best_match = i
            
            # If we found a good match, add it to insights
            if best_match is not None:
                orig_q = st.session_state.questions[best_match]
                insights[self._normalize_question(orig_q)] = user_answer
        
        return insights

    def _normalize_question(self, question):
        """Normalize a question to match between different formats."""
        # Convert to lowercase, remove punctuation, and strip whitespace
        normalized = question.lower().strip()
        
        # Remove common prefixes like "Q1: " or "Question: "
        if ":" in normalized:
            parts = normalized.split(":", 1)
            if parts[0].replace("q", "").replace("question", "").isdigit():
                normalized = parts[1].strip()
        
        return normalized