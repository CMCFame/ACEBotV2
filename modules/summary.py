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
        normalized = question_text.lower()
        normalized = re.sub(r'^(q\d+\s*:|question\s*\d+\s*:|\d+\.\s*)\s*', '', normalized)
        normalized = re.sub(r'[^\w\s\']', '', normalized) 
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _extract_qa_pairs_from_visible_messages(self):
        """
        Extracts question-answer pairs from st.session_state.visible_messages.
        Attempts to handle multi-bubble assistant messages and identify the actual question.
        """
        summary_pairs = []
        # Stores the most recent potential question text from an assistant message
        last_potential_question_text_from_assistant = None 
        # Stores the full content of the assistant message that contained the last_potential_question_text_from_assistant
        # This helps ensure the user's answer is in direct response to that specific assistant message bubble.
        content_of_last_assistant_message_with_question = None

        visible_messages = st.session_state.get("visible_messages", [])

        for i, message in enumerate(visible_messages):
            content = message.get("content", "")
            role = message.get("role", "")

            if role == "assistant":
                # Reset on every assistant message initially, then refine if it's a question
                last_potential_question_text_from_assistant = None 
                content_of_last_assistant_message_with_question = None
                
                current_message_question_text = ""
                # Prioritize "To continue with our question:"
                if "To continue with our question:" in content:
                    current_message_question_text = content.split("To continue with our question:")[-1].strip()
                # If no specific marker, check if the content itself looks like a question
                elif "?" in content:
                    # Try to get the last sentence with '?' as the question
                    sentences = re.split(r'(?<=[.!?])\s+', content)
                    for sentence in reversed(sentences):
                        if "?" in sentence:
                            current_message_question_text = sentence.strip()
                            break
                    if not current_message_question_text: # Fallback if sentence splitting fails
                        current_message_question_text = content.strip()
                
                if current_message_question_text and "?" in current_message_question_text:
                    last_potential_question_text_from_assistant = current_message_question_text
                    content_of_last_assistant_message_with_question = content


            elif role == "user" and last_potential_question_text_from_assistant and content_of_last_assistant_message_with_question:
                # Check if the immediately preceding message was the one that set our question context
                if i > 0 and visible_messages[i-1].get("content") == content_of_last_assistant_message_with_question:
                    user_answer = content
                    lower_user_answer = user_answer.lower().strip()
                    
                    ignored_phrases = [
                        "example", "show example", "give me an example", 
                        "example answer", "can you show me an example?", 
                        "?", "help", "i need help", "what do you mean"
                    ] # "yes", "no" can be valid short answers, keep them for now
                    
                    is_command = False
                    for phrase in ignored_phrases:
                        if phrase == lower_user_answer:
                            is_command = True
                            break
                    
                    if not is_command and len(user_answer.strip()) > 0:
                        summary_pairs.append((last_potential_question_text_from_assistant, user_answer))
                        # Reset after pairing to ensure this answer is used only once for this question
                        last_potential_question_text_from_assistant = None 
                        content_of_last_assistant_message_with_question = None 
        
        return summary_pairs

    def generate_conversation_summary(self):
        """Generates the .txt summary content using your original topic bucketing."""
        summary_pairs = self._extract_qa_pairs_from_visible_messages()
        
        summary_text = "# ACE Questionnaire Summary\n\n"
        summary_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        user_info = st.session_state.get("user_info", {})
        if user_info.get("name") or user_info.get("company"):
            summary_text += f"## User Information\n"
            if user_info.get("name"): summary_text += f"Name: {user_info['name']}\n"
            if user_info.get("company"): summary_text += f"Company: {user_info['company']}\n"
            summary_text += "\n"
        
        summary_text += "## Questionnaire Responses\n\n"

        if not summary_pairs:
            summary_text += "No question-answer pairs were extracted from the conversation.\n"
            return summary_text

        # Your original topic mapping and ordering for the text summary
        enhanced_topic_mapping = {
            "name": "Basic Information", "company": "Basic Information", "situation": "Basic Information", "frequent": "Basic Information", "callout type": "Basic Information", "callout occur": "Basic Information", "utility": "Basic Information",
            "employee": "Staffing Details", "staff": "Staffing Details", "role": "Staffing Details", "classification": "Staffing Details", "journeymen": "Staffing Details", "apprentice": "Staffing Details", "supervisor": "Staffing Details", "lineworker": "Staffing Details",
            "contact first": "Contact Process", "contact when": "Contact Process", "who do you contact": "Contact Process", "device": "Contact Process", "phone": "Contact Process", "call first": "Contact Process", "why are they contacted": "Contact Process", "dispatcher": "Contact Process", "coordinator": "Contact Process",
            "list": "List Management", "skip": "List Management", "traverse": "List Management", "straight down": "List Management", "order": "List Management", "pause": "List Management", "organized": "List Management", "criteria": "List Management",
            "required number": "Insufficient Staffing", "don't get": "Insufficient Staffing", "not enough": "Insufficient Staffing", "secondary list": "Insufficient Staffing", "part-time": "Insufficient Staffing", "whole list again": "Insufficient Staffing", "can't get enough": "Insufficient Staffing", "neighboring district": "Insufficient Staffing", "contractor": "Insufficient Staffing", "short-staffed": "Insufficient Staffing", "mutual aid": "Insufficient Staffing",
            "simultaneous": "Calling Logistics", "call again": "Calling Logistics", "second pass": "Calling Logistics", "nobody else accepts": "Calling Logistics", "all device": "Calling Logistics", "ensure quick response": "Calling Logistics",
            "change": "List Changes", "update": "List Changes", "overtime hours": "List Changes", "new hire": "List Changes", "transfer": "List Changes", "content of the list": "List Changes", "pay period": "List Changes", "scheduling changes": "List Changes",
            "tie": "Tiebreakers", "tiebreaker": "Tiebreakers", "seniority": "Tiebreakers", "alphabetical": "Tiebreakers", "rotating": "Tiebreakers",
            "text alert": "Additional Rules", "email": "Additional Rules", "rule": "Additional Rules", "shift": "Additional Rules", "exempt": "Additional Rules", "rest": "Additional Rules", "hour": "Additional Rules", "excuse": "Additional Rules", "declined callout": "Additional Rules", "holiday": "Additional Rules", "emergency response team": "Additional Rules"
        }
        topic_order = ["Basic Information", "Staffing Details", "Contact Process", "List Management", "Insufficient Staffing", "Calling Logistics", "List Changes", "Tiebreakers", "Additional Rules"]
        
        topic_buckets = OrderedDict()
        for topic in topic_order: topic_buckets[topic] = []
        topic_buckets["Other"] = [] # Fallback bucket

        for question, answer in summary_pairs:
            normalized_q_for_bucketing = self._normalize_question(question)
            # Include answer context for better bucketing if question is generic
            combined_text_for_bucketing = (normalized_q_for_bucketing + " " + answer.lower()).lower()
            
            best_match_topic = "Other" # Default to "Other"
            max_keyword_matches = 0

            for topic_name in topic_order:
                current_topic_keyword_matches = 0
                # Get keywords for the current topic_name
                keywords_for_this_topic = [kw for kw, mapped_topic in enhanced_topic_mapping.items() if mapped_topic == topic_name]
                for keyword in keywords_for_this_topic:
                    if keyword.lower() in combined_text_for_bucketing:
                        current_topic_keyword_matches += 1
                
                if current_topic_keyword_matches > max_keyword_matches:
                    max_keyword_matches = current_topic_keyword_matches
                    best_match_topic = topic_name
            
            topic_buckets[best_match_topic].append((question, answer))
        
        for topic_name, qa_list in topic_buckets.items():
            if qa_list: # Only print topics that have Q&A pairs
                summary_text += f"### {topic_name}\n\n"
                for q_text, a_text in qa_list:
                    summary_text += f"**Q: {q_text.strip()}**\n\n"
                    summary_text += f"A: {a_text.strip()}\n\n"
        return summary_text


    def get_responses_as_list(self):
        return self._extract_qa_pairs_from_visible_messages()

    def generate_progress_dashboard(self):
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

        # Mapping extracted Q&A to official questions
        mapped_answers_to_official_qs = {} 
        # To avoid mapping multiple AI questions to the same official question unless it's a better match
        official_q_best_match_score = {self._normalize_question(oq): 0.0 for oq in official_questions}


        for q_asked_by_ai, answer_given_by_user in extracted_qa_pairs:
            norm_q_asked_by_ai = self._normalize_question(q_asked_by_ai)
            
            best_official_q_for_this_ai_q = None
            highest_similarity_for_this_ai_q = 0.0

            for official_q_text in official_questions:
                norm_official_q = self._normalize_question(official_q_text)
                
                set_official = set(norm_official_q.split())
                set_asked = set(norm_q_asked_by_ai.split())
                
                if not set_official or not set_asked: continue
                
                intersection = len(set_official.intersection(set_asked))
                union = len(set_official.union(set_asked))
                similarity = intersection / union if union > 0 else 0.0
                
                if similarity > highest_similarity_for_this_ai_q:
                    highest_similarity_for_this_ai_q = similarity
                    best_official_q_for_this_ai_q = norm_official_q
            
            # If we found a sufficiently good official question match for the AI's question
            if best_official_q_for_this_ai_q and highest_similarity_for_this_ai_q > 0.5: # Similarity threshold
                # And if this mapping is better than any previous mapping for this official question
                if highest_similarity_for_this_ai_q > official_q_best_match_score.get(best_official_q_for_this_ai_q, 0.0):
                    mapped_answers_to_official_qs[best_official_q_for_this_ai_q] = answer_given_by_user
                    official_q_best_match_score[best_official_q_for_this_ai_q] = highest_similarity_for_this_ai_q
        
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

    # Keeping _extract_insights_from_conversation for now, as it was in your original.
    # Evaluate if it's still needed given the new dashboard logic.
    def _extract_insights_from_conversation(self):
        insights = {}
        keyword_to_question = {
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
        questions_from_file = st.session_state.get("questions", [])
        extracted_qa_pairs = self._extract_qa_pairs_from_visible_messages()

        for q_asked, answer_given in extracted_qa_pairs:
            norm_q_asked = self._normalize_question(q_asked)
            for keyword, question_indices in keyword_to_question.items():
                if keyword.lower() in norm_q_asked:
                    indices = question_indices if isinstance(question_indices, list) else [question_indices]
                    for index in indices:
                        if 0 < index <= len(questions_from_file):
                            official_q_text = questions_from_file[index - 1]
                            insights[self._normalize_question(official_q_text)] = answer_given
        return insights