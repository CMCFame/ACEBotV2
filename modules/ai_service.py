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
            """
            Robust example generation for testing - always provides relevant examples.
            Designed to support comprehensive testing of all question types.
            """
            if not last_question:
                return "We handle this based on our standard emergency response procedures."
            
            question_lower = last_question.lower()
            
            # COMPREHENSIVE example mapping for all major question types
            # This ensures every question type has a specific, relevant example
            
            # Basic Information Examples
            if any(word in question_lower for word in ["name", "company"]):
                return "John Smith from Metro Electric Utility"
            
            elif any(word in question_lower for word in ["type", "emergency", "situation", "callout", "handle", "respond"]):
                return "Power outages, downed lines, transformer failures, and gas leaks"
            
            elif any(word in question_lower for word in ["often", "frequency", "how many times", "occur", "happen"]):
                return "About 4-6 emergencies per week, more during storm season"
            
            # Staffing Examples
            elif any(word in question_lower for word in ["workers", "employees", "people", "staff", "how many"]) and not any(word in question_lower for word in ["device", "phone", "contact"]):
                return "Usually 3-4 field technicians plus 1 supervisor for standard emergencies"
            
            elif any(word in question_lower for word in ["job", "role", "skill", "certification", "qualification", "training"]):
                return "Licensed electricians, certified safety coordinators, and equipment operators"
            
            # Contact Process Examples  
            elif any(word in question_lower for word in ["first person", "contact first", "call first", "who first"]):
                return "The emergency dispatcher who coordinates all field responses"
            
            elif any(word in question_lower for word in ["why", "reason", "contact them"]):
                return "They have real-time access to crew locations and emergency protocols"
            
            elif any(word in question_lower for word in ["reach", "contact", "method", "phone", "radio", "communication"]):
                return "Emergency hotline first, then supervisor's cell phone, then radio backup"
            
            # List Management Examples
            elif any(word in question_lower for word in ["lists", "employee lists", "different lists"]):
                return "Yes, we have primary on-call, backup crew, and contractor lists"
            
            elif any(word in question_lower for word in ["how many lists", "number of lists"]):
                return "Three main lists: on-call technicians, backup staff, and emergency contractors"
            
            elif any(word in question_lower for word in ["organized", "organize", "arrangement", "structure"]):
                return "Lists are organized by job classification and overtime hours worked"
            
            # Calling Process Examples
            elif any(word in question_lower for word in ["order", "sequence", "call", "specific order"]):
                return "Yes, we call in order of least overtime hours worked, starting with senior technicians"
            
            elif any(word in question_lower for word in ["doesn't answer", "says no", "refuse", "decline"]):
                return "We move to the next person on the list and try the original person again later"
            
            # Backup Plans Examples
            elif any(word in question_lower for word in ["can't get enough", "not enough people", "short staff"]):
                return "We contact the backup list, then reach out to neighboring utility companies"
            
            elif any(word in question_lower for word in ["backup", "other places", "alternatives"]):
                return "Mutual aid agreements with nearby utilities and emergency contractor services"
            
            # List Changes Examples
            elif any(word in question_lower for word in ["lists change", "update", "modify"]):
                return "Yes, we update them monthly when overtime hours reset and staff changes"
            
            elif any(word in question_lower for word in ["how often", "frequency", "update"]) and "list" in question_lower:
                return "Monthly for overtime adjustments, immediately for new hires or departures"
            
            # Special Rules Examples
            elif any(word in question_lower for word in ["special rules", "timing", "when", "restrictions"]):
                return "Employees must have 8 hours rest between shifts per union agreement"
            
            elif any(word in question_lower for word in ["text", "email", "message", "notification"]):
                return "Yes, we send group text alerts for major outages affecting multiple areas"
            
            # Advanced Topics Examples
            elif any(word in question_lower for word in ["simultaneous", "same time", "multiple"]):
                return "Union rules require us to call employees individually in seniority order"
            
            elif any(word in question_lower for word in ["tie", "equal", "same hours", "tiebreaker"]):
                return "Seniority breaks ties, then alphabetical order by last name"
            
            elif any(word in question_lower for word in ["pause", "delay", "wait", "between"]):
                return "We wait 3 minutes for a response before moving to the next person"
            
            elif any(word in question_lower for word in ["device", "devices", "phone", "equipment"]) and any(word in question_lower for word in ["how many", "number"]):
                return "Each employee has a work cell phone and a backup pager"
            
            elif any(word in question_lower for word in ["which device", "first device", "contact first"]):
                return "Work cell phone first, then pager after 5 minutes if no response"
            
            # Catch-all for any unmatched questions
            else:
                return self._generate_testing_fallback_example(question_lower)
    
    def _generate_testing_fallback_example(self, question_lower):
        """Generate appropriate fallback examples for testing coverage."""
        
        # Additional pattern matching for edge cases
        if "vacation" in question_lower or "excuse" in question_lower:
            return "Employees on vacation or scheduled to work within 8 hours are excused"
        
        elif "contractor" in question_lower:
            return "We maintain a list of certified emergency contractors as backup"
        
        elif "supervisor" in question_lower and "contact" not in question_lower:
            return "Field supervisors must have emergency response certification"
        
        elif "location" in question_lower:
            return "We contact our three district offices or neighboring utility regions"
        
        elif "union" in question_lower:
            return "Union contract requires fair rotation and adequate rest periods"
        
        elif "emergency" in question_lower and "type" not in question_lower:
            return "All emergency calls take priority over scheduled maintenance work"
        
        else:
            # Final fallback - still useful for testing
            return "We follow our standard operating procedures with safety as the top priority"

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