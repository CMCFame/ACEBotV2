# modules/summary.py
import streamlit as st
from datetime import datetime
from collections import OrderedDict
from config import TOPIC_AREAS # Make sure TOPIC_AREAS is correctly imported
import re

class SummaryGenerator:
    def __init__(self):
        """Initialize the summary generator."""
        pass

    def _normalize_question(self, question_text):
        """Normalize a question to facilitate matching."""
        if not isinstance(question_text, str):
            return ""
        # Lowercase
        normalized = question_text.lower()
        # Remove common prefixes like "Q1: ", "Question: ", or just "1. "
        normalized = re.sub(r'^(q\d+\s*:|question\s*\d+\s*:|\d+\.\s*)\s*', '', normalized)
        # Remove punctuation that might hinder matching, keep alphanumeric and spaces
        normalized = re.sub(r'[^\w\s\']', '', normalized) # Keep apostrophes for contractions
        # Replace multiple whitespace characters with a single space
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _extract_qa_pairs_from_visible_messages(self):
        """
        Extracts question-answer pairs directly from st.session_state.visible_messages.
        This attempts to be more robust in identifying the actual question asked by the assistant.
        """
        summary_pairs = []
        last_assistant_question_content = None # Full content of the assistant's message that contained a question
        last_identified_question_text = ""     # The specific question text extracted

        for i, message in enumerate(st.session_state.get("visible_messages", [])):
            content = message.get("content", "")
            role = message.get("role", "")

            if role == "assistant":
                current_potential_question = ""
                # If the AI response includes "To continue with our question:", prioritize that as the question part
                if "To continue with our question:" in content:
                    current_potential_question = content.split("To continue with our question:")[-1].strip()
                # If an example is present, try to find a question after it
                elif "*Example:" in content or "Example:" in content:
                    # Split by example marker, take the part after the first marker
                    # This assumes the example text is followed by the question.
                    parts_after_example_marker = re.split(r'\*Example:|Example:', content, 1)
                    if len(parts_after_example_marker) > 1:
                        # Try to find where the example text itself ends (e.g., before "To continue...")
                        # This is heuristic; robust parsing of AI's formatted examples is complex.
                        # For now, we look for a question mark in the text following the example marker.
                        text_after_example = parts_after_example_marker[1]
                        # Remove the example text itself (heuristic: up to the next "To continue" or just find last '?')
                        if "To continue with our question:" in text_after_example:
                             current_potential_question = text_after_example.split("To continue with our question:")[-1].strip()
                        else: # Find last sentence with '?'
                            sentences = re.split(r'(?<=[.!?])\s+', text_after_example)
                            for sentence in reversed(sentences):
                                if "?" in sentence:
                                    current_potential_question = sentence.strip()
                                    break
                elif "?" in content: # General case if no specific markers found
                    current_potential_question = content
                
                # If we identified a potential question, extract the most likely question part
                if "?" in current_potential_question:
                    last_assistant_question_content = content # Store full original message for continuity matching
                    
                    final_question_text = ""
                    sentences = re.split(r'(?<=[.!?])\s+', current_potential_question)
                    for sentence in reversed(sentences):
                        if "?" in sentence:
                            final_question_text = sentence.strip()
                            break
                    last_identified_question_text = final_question_text if final_question_text else current_potential_question.strip()


            elif role == "user" and last_assistant_question_content:
                # Check if this user message directly follows the stored assistant message
                if i > 0 and st.session_state.visible_messages[i-1].get("content") == last_assistant_question_content:
                    user_answer = content
                    lower_user_answer = user_answer.lower().strip()
                    
                    # Avoid logging simple commands or very short non-answers as actual answers
                    ignored_phrases = ["example", "show example", "give me an example", 
                                       "example answer", "can you show me an example?", 
                                       "?", "help", "i need help", "what do you mean", 
                                       "ok", "yes", "no", "got it"] # Expand if needed
                    
                    if lower_user_answer not in ignored_phrases and len(user_answer) > 5: # Basic length check
                        if last_identified_question_text: # Ensure we have a question to pair with
                            summary_pairs.append((last_identified_question_text, user_answer))
                
                # Reset after processing a user message that could be an answer
                last_assistant_question_content = None
                last_identified_question_text = ""
        
        return summary_pairs

    def generate_conversation_summary(self):
        """Generate a comprehensive summary of the conversation for the .txt export."""
        summary_pairs = self._extract_qa_pairs_from_visible_messages()
        
        summary = "# ACE Questionnaire Summary\n\n"
        summary += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        user_info = st.session_state.get("user_info", {})
        if user_info.get("name") or user_info.get("company"):
            summary += f"## User Information\n"
            if user_info.get("name"):
                summary += f"Name: {user_info['name']}\n"
            if user_info.get("company"):
                summary += f"Company: {user_info['company']}\n"
            summary += "\n"
        
        summary += "## Questionnaire Responses\n\n"

        if not summary_pairs:
            summary += "No question-answer pairs were extracted from the conversation.\n"
            return summary

        # Retain topic bucketing from your original logic for the text summary
        enhanced_topic_mapping = {
            "name": "Basic Information", "company": "Basic Information", "situation": "Basic Information", "frequent": "Basic Information", "callout type": "Basic Information", "callout occur": "Basic Information",
            "employee": "Staffing Details", "staff": "Staffing Details", "role": "Staffing Details", "classification": "Staffing Details", "journeymen": "Staffing Details", "apprentice": "Staffing Details", "supervisor": "Staffing Details",
            "contact first": "Contact Process", "contact when": "Contact Process", "who do you contact": "Contact Process", "device": "Contact Process", "phone": "Contact Process", "call first": "Contact Process", "why are they contacted": "Contact Process",
            "list": "List Management", "skip": "List Management", "traverse": "List Management", "straight down": "List Management", "order": "List Management", "pause": "List Management", "organized": "List Management",
            "required number": "Insufficient Staffing", "don't get": "Insufficient Staffing", "not enough": "Insufficient Staffing", "secondary list": "Insufficient Staffing", "part-time": "Insufficient Staffing", "whole list again": "Insufficient Staffing", "can't get enough": "Insufficient Staffing", "neighboring district": "Insufficient Staffing", "contractor": "Insufficient Staffing", "short-staffed": "Insufficient Staffing",
            "simultaneous": "Calling Logistics", "call again": "Calling Logistics", "second pass": "Calling Logistics", "nobody else accepts": "Calling Logistics", "all device": "Calling Logistics", "ensure quick response": "Calling Logistics",
            "change": "List Changes", "update": "List Changes", "overtime hours": "List Changes", "new hire": "List Changes", "transfer": "List Changes", "content of the list": "List Changes", "pay period": "List Changes",
            "tie": "Tiebreakers", "tiebreaker": "Tiebreakers", "seniority": "Tiebreakers", "alphabetical": "Tiebreakers", "rotating": "Tiebreakers",
            "text alert": "Additional Rules", "email": "Additional Rules", "rule": "Additional Rules", "shift": "Additional Rules", "exempt": "Additional Rules", "rest": "Additional Rules", "hour": "Additional Rules", "excuse": "Additional Rules", "declined callout": "Additional Rules"
        }
        topic_order = ["Basic Information", "Staffing Details", "Contact Process", "List Management", "Insufficient Staffing", "Calling Logistics", "List Changes", "Tiebreakers", "Additional Rules"]
        
        topic_buckets = OrderedDict()
        for topic in topic_order: topic_buckets[topic] = []
        topic_buckets["Other"] = []
        
        for question, answer in summary_pairs:
            topic_assigned = False; best_match_topic = None; max_matches = 0
            combined_text = (self._normalize_question(question) + " " + answer.lower()).lower()
            for topic in topic_order:
                keyword_matches = 0
                topic_keywords = [kw for kw, t in enhanced_topic_mapping.items() if t == topic]
                for keyword in topic_keywords:
                    if keyword.lower() in combined_text: keyword_matches += 1
                if keyword_matches > max_matches:
                    max_matches = keyword_matches; best_match_topic = topic
            if max_matches > 0 and best_match_topic:
                topic_buckets[best_match_topic].append((question, answer)); topic_assigned = True
            if not topic_assigned: topic_buckets["Other"].append((question, answer))
        
        for topic, qa_pairs in topic_buckets.items():
            if qa_pairs:
                summary += f"### {topic}\n\n"
                for q_text, a_text in qa_pairs:
                    summary += f"**Q: {q_text}**\n\n"; summary += f"A: {a_text}\n\n"
        return summary

    def get_responses_as_list(self):
        """Extracts responses as a list of (question, answer) tuples for exports like CSV/Excel."""
        return self._extract_qa_pairs_from_visible_messages()

    def generate_progress_dashboard(self):
        """Generate a Markdown dashboard of questions and their mapped answers."""
        extracted_qa_pairs = self._extract_qa_pairs_from_visible_messages()
        official_questions = st.session_state.get("questions", [])
        
        dashboard = "# ACE Questionnaire Progress\n\n"
        dashboard += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        user_info = st.session_state.get("user_info", {})
        if user_info.get("name") or user_info.get("company"):
            dashboard += f"## User Information\n"
            if user_info.get("name"): dashboard += f"**Name:** {user_info['name']}\n"
            if user_info.get("company"): dashboard += f"**Company:** {user_info['company']}\n"
            dashboard += "\n"

        dashboard += "## Progress by Topic\n\n"
        topic_areas_covered = st.session_state.get("topic_areas_covered", {topic: False for topic in TOPIC_AREAS.keys()})
        for topic_key, display_name in TOPIC_AREAS.items():
            is_covered = topic_areas_covered.get(topic_key, False)
            status = "✅ Completed" if is_covered else "❌ Not Covered"
            dashboard += f"**{display_name}**: {status}\n"
        dashboard += "\n## All Questions and Answers (Attempted Mapping to Official List)\n\n"

        mapped_answers_to_official_qs = {} # Key: normalized official_q, Value: answer_given_by_user

        for official_q_text in official_questions:
            norm_official_q = self._normalize_question(official_q_text)
            best_match_score = -1.0 # Use -1 to ensure any match is better
            best_answer = None
            
            for q_asked_by_ai, answer_given_by_user in extracted_qa_pairs:
                norm_q_asked_by_ai = self._normalize_question(q_asked_by_ai)
                
                set_official = set(norm_official_q.split())
                set_asked = set(norm_q_asked_by_ai.split())
                
                if not set_official or not set_asked: continue # Cannot compare if one is empty
                
                intersection = len(set_official.intersection(set_asked))
                union = len(set_official.union(set_asked))
                similarity = intersection / union if union > 0 else 0.0
                
                # If this AI-asked question is a better match for the current official question
                if similarity > best_match_score:
                    best_match_score = similarity
                    # If similarity is high enough, consider it a match
                    if similarity > 0.5: # Threshold for considering a match (tune this value)
                        best_answer = answer_given_by_user
            
            if best_answer:
                mapped_answers_to_official_qs[norm_official_q] = best_answer
        
        answers_count = len(mapped_answers_to_official_qs)
        dashboard += f"**Questions Answered (Mapped):** {answers_count} of {len(official_questions)}\n\n"

        for i, official_q_text in enumerate(official_questions):
            norm_official_q = self._normalize_question(official_q_text)
            dashboard += f"### Q{i+1}: {official_q_text}\n\n"
            if norm_official_q in mapped_answers_to_official_qs:
                dashboard += f"{mapped_answers_to_official_qs[norm_official_q]}\n\n"
            else:
                dashboard += f"*No confidently mapped answer found for this question.*\n\n"
        
        return dashboard

    def _extract_insights_from_conversation(self):
        """
        Legacy method for keyword-based insight extraction. 
        Consider if this is still needed or if the Q&A pair extraction and mapping is sufficient.
        """
        insights = {}
        keyword_to_question = { # From your original file
            "name and company": 1, "situation": 2, "employees required": 3, "call first": 4, "why": 5, 
            "devices have": 6, "device first": 7, "type of devices": 8, "same list": 9, "lists total": 10, 
            "job classification": 11, "other attribute": 12, "how do you call": 13, "straight down": 14, 
            "skip around": [15, 16, 17, 18], "pauses": 19, "don't get required": 20, "different list": 21, 
            "different location": 22, "offer position": 23, "consider list again": 24, "call list again": 25, 
            "do differently": 26, "calling simultaneously": [27, 28], "call again if nobody": 29, "first pass": 30, 
            "change over time": 31, "when change": 32, "order change": 33, "content change": 34, 
            "when content change": 35, "how content change": 36, "tie breakers": 37, "first tiebreaker": 38, 
            "second tiebreaker": 39, "third tiebreaker": 40, "email or text": 41, "rules prevent": 42, "rules excuse": 43
        }
        
        conversation_pairs = [] # Reuse extraction from _extract_qa_pairs_from_visible_messages for consistency
        raw_pairs = self._extract_qa_pairs_from_visible_messages() # (question_asked_by_ai, user_answer)
        for asst_msg, user_msg in raw_pairs:
            if len(user_msg) > 10: # Substantive answer
                for keyword, question_numbers in keyword_to_question.items():
                    if keyword.lower() in self._normalize_question(asst_msg): # Match keyword in AI's question
                        q_list = question_numbers if isinstance(question_numbers, list) else [question_numbers]
                        for q_num in q_list:
                            if 0 < q_num <= len(st.session_state.get("questions",[])):
                                official_question = st.session_state.questions[q_num-1]
                                insights[self._normalize_question(official_question)] = user_msg
        return insights