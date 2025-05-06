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