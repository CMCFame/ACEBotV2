# modules/ai_service.py
import boto3
import streamlit as st
import json
import os
import re
from config import BEDROCK_MODEL_ID, BEDROCK_AWS_REGION, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

class AIService:
    def __init__(self, aws_region=BEDROCK_AWS_REGION):
        """Initialize the AI service."""
        try:
            aws_access_key_id = st.secrets.aws.get("aws_access_key_id") if hasattr(st, 'secrets') and 'aws' in st.secrets else os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = st.secrets.aws.get("aws_secret_access_key") if hasattr(st, 'secrets') and 'aws' in st.secrets else os.getenv('AWS_SECRET_ACCESS_KEY')

            if aws_access_key_id and aws_secret_access_key:
                self.client = boto3.client(
                    service_name='bedrock-runtime', region_name=aws_region,
                    aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
                )
            else:
                self.client = boto3.client(service_name='bedrock-runtime', region_name=aws_region)
        except Exception as e:
            st.error(f"❌ Failed to initialize Bedrock client: {e}")
            self.client = None

    def analyze_comprehensive_answer(self, user_input):
        """
        Analyze if user provided comprehensive answer covering multiple topics.
        Returns topics that might be covered in the response.
        """
        if len(user_input.strip()) < 50:  # Short answers unlikely to be comprehensive
            return []
        
        # Enhanced pattern matching for comprehensive answers
        topic_indicators = {
            "contact_process": ["call first", "contact", "dispatcher", "supervisor", "device", "phone"],
            "list_management": ["list", "order", "seniority", "classification", "skip", "straight"],
            "staffing_details": ["employee", "technician", "crew", "role", "certification", "lineman"],
            "calling_logistics": ["simultaneous", "union", "individual", "same time", "one at a time"],
            "insufficient_staffing": ["not enough", "required number", "different list", "mutual aid"],
            "list_changes": ["change", "update", "quarterly", "over time", "hire", "terminate"],
            "tiebreakers": ["tie", "tiebreaker", "overtime", "seniority", "alphabetical"],
            "additional_rules": ["email", "text", "shift", "hours", "vacation", "excuse"]
        }
        
        user_lower = user_input.lower()
        covered_topics = []
        
        for topic, keywords in topic_indicators.items():
            matches = sum(1 for keyword in keywords if keyword in user_lower)
            if matches >= 2:  # Require multiple keyword matches
                covered_topics.append(topic)
        
        return covered_topics

    def check_response_type(self, question, user_input):
        """Enhanced response type checking."""
        # Handle help/example requests quickly
        help_indicators = ["example", "help", "what do you mean", "explain", "clarify"]
        if any(indicator in user_input.lower() for indicator in help_indicators):
            return False
        
        # If it's a substantial response (>20 chars), likely an answer
        if len(user_input.strip()) > 20:
            return True
            
        # Use AI for edge cases
        system_prompt = "Determine if this is a direct answer or help request. Respond only 'ANSWER' or 'QUESTION'."
        messages_for_check = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Question: '{question}' Response: '{user_input}' - Is this an answer or help request?"}
        ]
        response = self.get_response(messages_for_check, max_tokens=10, temperature=0.0)
        return "ANSWER" in response.upper() if response else True

    def extract_user_info(self, user_input):
        """Enhanced user info extraction."""
        # Quick pattern matching first
        patterns = {
            'name': r'(?:name is|i\'m|my name is|this is)\s+([a-zA-Z\s]+)',
            'company': r'(?:company|work at|from)\s+([a-zA-Z\s&]+)'
        }
        
        extracted = {"name": "", "company": ""}
        user_lower = user_input.lower()
        
        for field, pattern in patterns.items():
            match = re.search(pattern, user_lower)
            if match:
                extracted[field] = match.group(1).strip().title()
        
        # If patterns didn't work, use AI
        if not (extracted["name"] or extracted["company"]):
            system_prompt = (
                "Extract name and company from user response. "
                "Format: NAME: [name], COMPANY: [company]. Use 'unknown' if not found."
            )
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"User response: {user_input}"}
            ]
            response = self.get_response(messages, max_tokens=100, temperature=0.0)
            
            try:
                if "NAME:" in response and "COMPANY:" in response:
                    name_match = re.search(r'NAME:\s*([^,]+)', response)
                    company_match = re.search(r'COMPANY:\s*(.+)', response)
                    
                    if name_match and name_match.group(1).lower() != "unknown":
                        extracted["name"] = name_match.group(1).strip()
                    if company_match and company_match.group(1).lower() != "unknown":
                        extracted["company"] = company_match.group(1).strip()
            except:
                pass
        
        return extracted

    def process_special_message_types(self, user_input):
        """Enhanced special message detection."""
        lower_input = user_input.lower().strip()
        
        # Quick exact matches
        exact_matches = {
            "example": {"type": "example_request"},
            "show example": {"type": "example_request"},
            "help": {"type": "help_request"},
            "i need help": {"type": "help_request"},
            "summary": {"type": "summary_request"},
            "download": {"type": "summary_request"},
            "done": {"type": "summary_request"},
            "finished": {"type": "summary_request"},
            "complete": {"type": "summary_request"},
            "that's all": {"type": "summary_request"},
            "nothing else": {"type": "summary_request"},
            "none": {"type": "summary_request"},
            "no": {"type": "summary_request"}
        }
        
        if lower_input in exact_matches:
            return exact_matches[lower_input]
        
        # Partial matches
        if any(phrase in lower_input for phrase in ["can you show", "give me an example"]):
            return {"type": "example_request"}
        
        if any(phrase in lower_input for phrase in ["what do you mean", "explain", "clarify"]):
            return {"type": "help_request"}
        
        if any(phrase in lower_input for phrase in ["that's everything", "all done", "we're done"]):
            return {"type": "summary_request"}
        
        return {"type": "regular_input"}

    def get_example_response(self, last_question):
        """Improved example generation."""
        # Extract key topic from question
        topic_keywords = {
            "contact": "We call the on-duty supervisor first because they coordinate crew assignments.",
            "device": "Each employee has a company phone and personal backup. We try the company phone first.",
            "list": "We have 3 lists: primary on-call, secondary backup, and emergency contractors.",
            "number": "Typically 3-4 people: one supervisor and 2-3 technicians depending on the situation.",
            "why": "This ensures consistent decision-making and proper resource allocation.",
            "when": "During storm season we might get 10-15 callouts, but normally it's 3-5 per week.",
            "simultaneous": "Union rules require us to call in seniority order, so no simultaneous calling.",
            "change": "Lists update quarterly when overtime hours reset, plus any time someone transfers.",
            "tie": "If overtime is equal, we use seniority. If that's equal too, alphabetical by last name."
        }
        
        question_lower = last_question.lower() if last_question else ""
        
        for keyword, example in topic_keywords.items():
            if keyword in question_lower:
                return example
        
        # Fallback to AI generation
        system_message = f"""
        Provide a brief, specific example answer for: "{last_question}"
        Make it realistic for a utility company. Keep it under 20 words.
        Don't include prefixes like "Example:" - just the example text.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": "Generate the example now."}
        ]
        
        response = self.get_response(messages, max_tokens=50, temperature=0.7)
        return response.strip() if response else "We handle this based on our standard procedures."

    def _clean_and_prepare_messages(self, messages):
        """Clean and prepare messages for the API."""
        consolidated_system_prompt = ""
        claude_messages = []
        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
            role = msg["role"]
            content = str(msg["content"]) if msg["content"] is not None else ""
            
            if role == "system":
                consolidated_system_prompt += content.strip() + "\n\n"
            elif role in ["user", "assistant"] and (content.strip() or role == "user"):
                claude_messages.append({"role": role, "content": content.strip()})
        return consolidated_system_prompt.strip(), claude_messages

    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        """Get response from the AI service."""
        if not self.client:
            return "Bedrock client not initialized. Please check AWS credentials configuration."

        try:
            system_prompt, claude_messages = self._clean_and_prepare_messages(messages)
            
            api_call_messages = []

            if system_prompt:
                if not claude_messages:
                    api_call_messages = [{"role": "user", "content": "Please proceed based on your instructions."}]
                elif claude_messages[0]["role"] == "assistant":
                    api_call_messages = [{"role": "user", "content": "Context."}] 
                    api_call_messages.extend(claude_messages)
                else:
                    api_call_messages = claude_messages
            else:
                api_call_messages = claude_messages

            if not api_call_messages and not system_prompt:
                 return "Error: No messages or system prompt to process."

            body = {
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_call_messages
            }
            
            if system_prompt:
                body["system"] = system_prompt

            if not body["messages"] and "system" not in body:
                 return "Error: No content to send to Bedrock model."
            if not body["messages"] and "system" in body and not body["system"]:
                 return "Error: Empty system prompt and no messages."

            response = self.client.invoke_model(
                modelId=BEDROCK_MODEL_ID,
                contentType='application/json',
                accept='application/json',
                body=json.dumps(body)
            )
            response_body = json.loads(response.get('body').read())

            if response_body.get("content") and isinstance(response_body["content"], list):
                text_content = ""
                for block in response_body["content"]:
                    if block.get("type") == "text":
                        text_content += block.get("text", "")
                return text_content.strip()
            else:
                error_type = response_body.get("error", {}).get("type")
                error_message = response_body.get("error", {}).get("message")
                if error_type and error_message:
                    st.error(f"Bedrock API Error ({error_type}): {error_message}")
                    return f"Error from Bedrock: {error_message}"
                st.warning(f"Unexpected response structure from Bedrock: {response_body}")
                return "Error: Could not parse response from Bedrock."

        except Exception as e: 
            st.error(f"Bedrock API Call Error: {str(e)}")
            return f"Error calling Bedrock API: {str(e)}"