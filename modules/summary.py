# modules/summary.py
import streamlit as st
from datetime import datetime
from collections import OrderedDict
from config import TOPIC_AREAS
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
        # Remove question numbering
        normalized = re.sub(r'^(q\d+\s*:|question\s*\d+\s*:|\d+\.\s*)\s*', '', normalized)
        # Remove punctuation but keep apostrophes
        normalized = re.sub(r'[^\w\s\']', '', normalized) 
        # Normalize whitespace
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        return normalized

    def _extract_qa_pairs_from_visible_messages(self):
        """
        Extract question-answer pairs from visible messages with improved logic.
        Handles multi-part assistant messages and better question detection.
        """
        qa_pairs = []
        visible_messages = st.session_state.get("visible_messages", [])
        
        if not visible_messages:
            return qa_pairs
        
        i = 0
        while i < len(visible_messages):
            message = visible_messages[i]
            
            # Look for assistant messages that contain questions
            if message.get("role") == "assistant":
                content = message.get("content", "")
                question_text = self._extract_question_from_content(content)
                
                if question_text:
                    # Look for the next user response
                    next_user_response = self._find_next_user_response(visible_messages, i)
                    
                    if next_user_response and self._is_valid_answer(next_user_response):
                        qa_pairs.append((question_text, next_user_response))
            
            i += 1
        
        return qa_pairs

    def _extract_question_from_content(self, content):
        """Extract the main question from assistant message content."""
        if not content or "?" not in content:
            return None
        
        # Check for structured question format first
        if "To continue with our question:" in content:
            question_part = content.split("To continue with our question:")[-1].strip()
            if "?" in question_part:
                return question_part.strip()
        
        # Look for question boxes in HTML content
        if "Question:" in content:
            lines = content.split('\n')
            for line in lines:
                if "Question:" in line and "?" in line:
                    # Extract text after "Question:" marker
                    question = line.split("Question:")[-1].strip()
                    # Clean up HTML tags if present
                    question = re.sub(r'<[^>]+>', '', question).strip()
                    if question and "?" in question:
                        return question
        
        # Fall back to finding the last sentence with a question mark
        sentences = re.split(r'[.!]\s+', content)
        for sentence in reversed(sentences):
            if "?" in sentence:
                # Clean up HTML and extra formatting
                question = re.sub(r'<[^>]+>', '', sentence).strip()
                question = re.sub(r'\*+', '', question).strip()
                if len(question) > 10:  # Avoid very short questions
                    return question
        
        return None

    def _find_next_user_response(self, messages, start_index):
        """Find the next substantive user response after the given index."""
        for i in range(start_index + 1, len(messages)):
            msg = messages[i]
            if msg.get("role") == "user":
                response = msg.get("content", "").strip()
                if response:
                    return response
            elif msg.get("role") == "assistant":
                # If we hit another assistant message, we've gone too far
                break
        return None

    def _is_valid_answer(self, response):
        """Check if a user response is a valid answer (not just a command)."""
        if not response:
            return False
        
        response_lower = response.lower().strip()
        
        # Filter out obvious non-answers
        non_answers = [
            "example", "show example", "give me an example", "can you show me an example?",
            "help", "i need help", "what do you mean", "?", "explain",
            "summary", "download", "yes", "no" # These might be valid in context but are often commands
        ]
        
        # If it's a very short response, be more selective
        if len(response.split()) <= 2:
            return response_lower not in non_answers
        
        # Longer responses are generally valid answers
        return True

    def _match_to_official_question(self, extracted_question, official_questions):
        """Match an extracted question to an official question using improved similarity."""
        if not extracted_question:
            return None
        
        norm_extracted = self._normalize_question(extracted_question)
        best_match = None
        best_score = 0.0
        
        for official_q in official_questions:
            norm_official = self._normalize_question(official_q)
            
            # Calculate word overlap score
            extracted_words = set(norm_extracted.split())
            official_words = set(norm_official.split())
            
            if not extracted_words or not official_words:
                continue
            
            # Jaccard similarity
            intersection = extracted_words.intersection(official_words)
            union = extracted_words.union(official_words)
            jaccard = len(intersection) / len(union) if union else 0
            
            # Boost score for key matching terms
            key_terms_bonus = 0
            key_terms = ['call', 'first', 'contact', 'list', 'employee', 'device', 'number', 'why', 'how']
            for term in key_terms:
                if term in norm_extracted and term in norm_official:
                    key_terms_bonus += 0.1
            
            total_score = jaccard + key_terms_bonus
            
            if total_score > best_score and total_score > 0.3:  # Minimum threshold
                best_score = total_score
                best_match = official_q
        
        return best_match

    def generate_conversation_summary(self):
        """Generate the main conversation summary for download."""
        qa_pairs = self._extract_qa_pairs_from_visible_messages()
        
        summary_text = "# ACE Questionnaire Summary\n\n"
        summary_text += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        user_info = st.session_state.get("user_info", {})
        if user_info.get("name") or user_info.get("company"):
            summary_text += f"## User Information\n"
            if user_info.get("name"): 
                summary_text += f"Name: {user_info['name']}\n"
            if user_info.get("company"): 
                summary_text += f"Company: {user_info['company']}\n"
            summary_text += "\n"
        
        summary_text += "## Questionnaire Responses\n\n"

        if not qa_pairs:
            summary_text += "No question-answer pairs were extracted from the conversation.\n"
            summary_text += "\n### Debug Information\n"
            summary_text += f"Total visible messages: {len(st.session_state.get('visible_messages', []))}\n"
            return summary_text

        # Organize by topic areas
        topic_buckets = self._organize_qa_by_topics(qa_pairs)
        
        for topic_name, topic_qa_list in topic_buckets.items():
            if topic_qa_list:
                summary_text += f"### {topic_name}\n\n"
                for question, answer in topic_qa_list:
                    summary_text += f"**Q: {question}**\n\n"
                    summary_text += f"A: {answer}\n\n"
        
        return summary_text

    def _organize_qa_by_topics(self, qa_pairs):
        """Organize Q&A pairs by topic areas."""
        # Topic keywords mapping
        topic_keywords = {
            "Basic Information": ["name", "company", "situation", "type", "callout", "frequency"],
            "Staffing Details": ["employees", "required", "staff", "roles", "classification", "how many"],
            "Contact Process": ["call first", "contact", "devices", "phone", "why", "who"],
            "List Management": ["list", "order", "straight down", "skip", "traverse", "based on"],
            "Insufficient Staffing": ["required number", "not enough", "different list", "whole list", "offer position"],
            "Calling Logistics": ["simultaneously", "same time", "call again", "second pass"],
            "List Changes": ["change", "update", "over time", "when", "content"],
            "Tiebreakers": ["tie", "tiebreaker", "overtime", "seniority"],
            "Additional Rules": ["email", "text", "rules", "prevent", "excuse", "shift"]
        }
        
        # Initialize buckets
        topic_buckets = OrderedDict()
        for topic in TOPIC_AREAS.values():
            topic_buckets[topic] = []
        topic_buckets["Other"] = []
        
        for question, answer in qa_pairs:
            question_lower = question.lower()
            answer_lower = answer.lower()
            combined_text = question_lower + " " + answer_lower
            
            best_topic = "Other"
            max_matches = 0
            
            for topic_name, keywords in topic_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in combined_text)
                if matches > max_matches:
                    max_matches = matches
                    best_topic = topic_name
            
            topic_buckets[best_topic].append((question, answer))
        
        return topic_buckets

    def generate_progress_dashboard(self):
        """Generate the progress dashboard with better question mapping."""
        qa_pairs = self._extract_qa_pairs_from_visible_messages()
        official_questions = st.session_state.get("questions", [])
        
        dashboard = "# ACE Questionnaire Progress\n\n"
        dashboard += f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        
        user_info = st.session_state.get("user_info", {})
        if user_info.get("name") or user_info.get("company"):
            dashboard += f"## User Information\n"
            if user_info.get("name"): 
                dashboard += f"**Name:** {user_info['name']}\n"
            if user_info.get("company"): 
                dashboard += f"**Company:** {user_info['company']}\n"
            dashboard += "\n"

        dashboard += "## Progress by Topic\n\n"
        topic_areas_covered = st.session_state.get("topic_areas_covered", {})
        for topic_key, display_name in TOPIC_AREAS.items():
            is_covered = topic_areas_covered.get(topic_key, False)
            status = "✅ Completed" if is_covered else "❌ Not Covered"
            dashboard += f"**{display_name}**: {status}\n"
        
        dashboard += f"\n## Extracted Question-Answer Pairs\n\n"
        dashboard += f"**Total Q&A Pairs Extracted:** {len(qa_pairs)}\n\n"
        
        # Map extracted Q&A to official questions
        mapped_answers = {}
        for question, answer in qa_pairs:
            matched_official = self._match_to_official_question(question, official_questions)
            if matched_official:
                mapped_answers[matched_official] = answer
        
        dashboard += f"**Questions Answered (Mapped to Official List):** {len(mapped_answers)} of {len(official_questions)}\n\n"
        
        dashboard += "## Official Questions Coverage\n\n"
        for i, official_q in enumerate(official_questions):
            dashboard += f"### Q{i+1}: {official_q}\n\n"
            if official_q in mapped_answers:
                dashboard += f"**Answer:** {mapped_answers[official_q]}\n\n"
            else:
                dashboard += f"*No answer found for this question.*\n\n"
        
        # Add debug section
        dashboard += "## Debug Information\n\n"
        dashboard += f"**Extracted Q&A Pairs:**\n\n"
        for i, (q, a) in enumerate(qa_pairs, 1):
            dashboard += f"{i}. **Q:** {q}\n   **A:** {a}\n\n"
        
        return dashboard

    def get_responses_as_list(self):
        """Get responses as a list for export."""
        return self._extract_qa_pairs_from_visible_messages()

    # Keep the legacy method for backward compatibility
    def _extract_insights_from_conversation(self):
        """Legacy method - kept for compatibility."""
        return {}