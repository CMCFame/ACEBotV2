# modules/ai_service.py
import boto3
import streamlit as st
import json
import os
from config import BEDROCK_MODEL_ID, BEDROCK_AWS_REGION, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

class AIService:
    def __init__(self, aws_region=BEDROCK_AWS_REGION):
        """Initialize the AI service with AWS Bedrock client."""
        try:
            aws_access_key_id = None
            aws_secret_access_key = None
            
            if hasattr(st, 'secrets'):
                if 'aws' in st.secrets:
                    aws_access_key_id = st.secrets.aws.get("aws_access_key_id")
                    aws_secret_access_key = st.secrets.aws.get("aws_secret_access_key")

            if not aws_access_key_id:
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')

            if aws_access_key_id and aws_secret_access_key:
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                try:
                    self.client = boto3.client(service_name='bedrock-runtime', region_name=aws_region)
                except Exception as default_e:
                    self.client = None
                    st.error(f"❌ AWS credential setup failed: {default_e}")
                    
        except Exception as e:
            st.error(f"❌ Failed to initialize Bedrock client: {e}")
            self.client = None

    def _clean_and_prepare_messages(self, messages):
        """Clean messages and prepare them for Claude, preserving the main system prompt."""
        if not messages:
            return "", []
        
        # Extract the main system prompt (should be first message)
        main_system_prompt = ""
        if messages[0].get("role") == "system":
            main_system_prompt = messages[0]["content"]
            remaining_messages = messages[1:]
        else:
            remaining_messages = messages
        
        # Clean and validate user/assistant messages
        claude_messages = []
        for msg in remaining_messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
                
            role = msg["role"]
            content = str(msg["content"]) if msg["content"] is not None else ""
            
            # FIXED: Convert system messages to user messages with clear markers
            if role == "system":
                # Convert system instructions to user messages so Claude sees them
                content = f"[INSTRUCTION]: {content}"
                role = "user"
            
            # Only keep non-empty user/assistant messages
            if role in ["user", "assistant"] and content.strip():
                claude_messages.append({"role": role, "content": content.strip()})
        
        return main_system_prompt, claude_messages

    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        """Get a response from the Bedrock API using Claude."""
        if not self.client:
            return "Bedrock client not initialized. Please check AWS credentials configuration."

        try:
            system_prompt, claude_messages = self._clean_and_prepare_messages(messages)
            
            # Ensure we have at least one message for Claude
            if not claude_messages:
                return "No valid messages to process."

            body = {
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": claude_messages
            }
            
            # Add system prompt if available
            if system_prompt and system_prompt.strip(): 
                body["system"] = system_prompt.strip()

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
            elif response_body.get("completion"):
                return response_body.get("completion").strip()
            else:
                return "Error: Could not parse response from Bedrock."

        except Exception as e: 
            return f"Error calling Bedrock API: {e}"

    def extract_user_info(self, user_input):
        """Extract user name and company name from the first response using Claude."""
        system_prompt = (
            "You are an expert text analysis assistant. Your task is to extract the user's name and company name "
            "from their response to the question 'Could you please provide your name and your company name?'.\n\n"
            "Respond ONLY with the following exact format:\n"
            "NAME: [extracted name or unknown], COMPANY: [extracted company or unknown]\n\n"
            "Do not include any other text, greetings, or explanations. Only the 'NAME: ..., COMPANY: ...' line."
        )

        extract_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User response: {user_input}"}
        ]

        extract_response = self.get_response(extract_messages, max_tokens=100, temperature=0.0)

        try:
            name_part = "unknown"
            company_part = "unknown"

            raw_response_str = str(extract_response).strip()

            name_marker = "NAME:"
            company_marker = "COMPANY:"

            name_start_index = raw_response_str.find(name_marker)
            company_start_index = raw_response_str.find(company_marker)

            if name_start_index != -1:
                name_value_start = name_start_index + len(name_marker)
                if company_start_index != -1 and company_start_index > name_start_index:
                    name_str_candidate = raw_response_str[name_value_start:company_start_index].replace(",", "").strip()
                else:
                    name_str_candidate = raw_response_str[name_value_start:].strip()
                
                if name_str_candidate and name_str_candidate.lower() != "unknown":
                    name_part = name_str_candidate

            if company_start_index != -1:
                company_value_start = company_start_index + len(company_marker)
                company_str_candidate = raw_response_str[company_value_start:].strip()

                if company_str_candidate and company_str_candidate.lower() != "unknown":
                    company_part = company_str_candidate
            
            return {
                "name": name_part if name_part != "unknown" else "",
                "company": company_part if company_part != "unknown" else ""
            }
        except Exception as e:
            print(f"Error extracting user info with Claude: {e}. Response was: {extract_response}")
            return {"name": "", "company": ""}

    def check_response_type(self, question, user_input):
        """Determine if a user message is an answer or a question/request using Claude."""
        system_prompt = "You are an AI assistant that determines if a user's message is a direct answer to a given question or if it's a request for help/clarification. Respond with only the single word 'ANSWER' or the single word 'QUESTION'."
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The question asked was: '{question}'. The user responded: '{user_input}'. Is the user's response a direct answer to the question, or is it a request for help or clarification? Respond with only the single word 'ANSWER' or 'QUESTION'."}
        ]

        response = self.get_response(messages, max_tokens=10, temperature=0.0)
        return "ANSWER" in response.upper()

    def process_special_message_types(self, user_input):
        """Process special message types like example requests."""
        lower_input = user_input.lower().strip()

        if lower_input in ["example", "show example", "give me an example", "example answer", "can you show me an example?"]:
            return {"type": "example_request"}
        if lower_input in ["?", "help", "i need help", "what do you mean"]:
            return {"type": "help_request"}
        if lower_input in ["summary", "download", "download summary", "get summary", "show summary", "yes", "provide summary"]:
            return {"type": "summary_request"}
        if any(phrase in lower_input for phrase in ["already answered", "not helpful", "i already responded", "already responded"]):
            return {"type": "frustration", "subtype": "summary_request"}
        return {"type": "regular_input"}

    def get_example_response(self, last_question):
        """Get a consistently formatted example response using Claude."""
        system_message = f"""
You are providing a brief example answer for a utility company callout process question.
The question you need to provide an example for is: "{last_question}"

Your task is to provide ONLY the example text itself. It should be short (1-2 sentences) and specific.
Do NOT include any prefixes like "Example:", "Here's an example:", or any explanations.
Do NOT repeat the question.
Just output the example sentence(s).

For instance, if the question was about who to contact first, a good direct example output from you would be:
"We contact the on-call supervisor first as they are responsible for assessing the situation and dispatching the appropriate crew."
"""
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": "Provide the example answer now."}
        ]

        example_response_text = self.get_response(messages, max_tokens=100, temperature=0.7)
        return example_response_text.strip()