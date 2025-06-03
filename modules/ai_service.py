# modules/ai_service.py - Fixed version for ACEBotV2
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
                self.client = boto3.client(service_name='bedrock-runtime', region_name=aws_region)
                    
        except Exception as e:
            st.error(f"Failed to initialize Bedrock client: {e}")
            self.client = None

    def _separate_system_prompt(self, messages):
        """Separates the system prompt from the message list for Claude API."""
        system_prompt = ""
        chat_messages = []
        
        if not messages:
            return system_prompt, chat_messages
        
        # Get system prompt from first message if it's a system message
        if messages and messages[0].get("role") == "system":
            system_prompt = messages[0].get("content", "")
            remaining_messages = messages[1:]
        else:
            remaining_messages = messages
        
        # Process remaining messages, ensuring proper alternating user/assistant pattern
        last_role = None
        for msg in remaining_messages:
            if not isinstance(msg, dict):
                continue
                
            role = msg.get("role", "")
            content = msg.get("content", "")
            
            # Skip empty content
            if not content or not content.strip():
                continue
                
            if role in ["user", "assistant"]:
                # Ensure alternating pattern - if same role appears twice, skip the duplicate
                if role != last_role:
                    chat_messages.append({"role": role, "content": content.strip()})
                    last_role = role
            elif role == "system":
                # Convert additional system messages to user messages
                if content.strip() and last_role != "user":
                    chat_messages.append({"role": "user", "content": f"[System note: {content.strip()}]"})
                    last_role = "user"
        
        # Ensure the conversation ends with a user message for Claude
        if chat_messages and chat_messages[-1]["role"] == "assistant":
            chat_messages.append({"role": "user", "content": "Please continue."})
        
        return system_prompt, chat_messages

    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        """Get a response from the Bedrock API using Claude."""
        if not self.client:
            return "Bedrock client not initialized. Please check AWS credentials configuration."

        try:
            system_prompt, claude_messages = self._separate_system_prompt(messages)
            
            # Ensure we have at least one message for Claude
            if not claude_messages:
                if system_prompt.strip():
                    claude_messages = [{"role": "user", "content": "Please begin the conversation."}]
                else:
                    return "Cannot send an empty request to the AI."

            body = {
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": claude_messages
            }
            
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
        extract_messages = [
            {"role": "user", "content": f"Extract the user name and company name from this response to the question 'Could you please provide your name and your company name?'\n\nUser response: {user_input}\n\nRespond ONLY with: NAME: [name or unknown], COMPANY: [company or unknown]"}
        ]

        extract_response = self.get_response(extract_messages, max_tokens=100, temperature=0.0)

        try:
            name_part = "unknown"
            company_part = "unknown"

            if "NAME:" in extract_response:
                name_start = extract_response.find("NAME:") + 5
                if "COMPANY:" in extract_response:
                    name_end = extract_response.find("COMPANY:")
                    name_part = extract_response[name_start:name_end].replace(",", "").strip()
                else:
                    name_part = extract_response[name_start:].strip()

            if "COMPANY:" in extract_response:
                company_start = extract_response.find("COMPANY:") + 8
                company_part = extract_response[company_start:].strip()
            
            return {
                "name": name_part if name_part != "unknown" else "",
                "company": company_part if company_part != "unknown" else ""
            }
        except Exception as e:
            return {"name": "", "company": ""}

    def check_response_type(self, question, user_input):
        """Determine if a user message is an answer or a question/request using Claude."""
        if not question or not user_input:
            return True  # Default to treating as answer
            
        messages = [
            {"role": "user", "content": f"The question asked was: '{question}'. The user responded: '{user_input}'. Is the user's response a direct answer to the question, or is it a request for help or clarification? Respond with only 'ANSWER' or 'QUESTION'."}
        ]

        response = self.get_response(messages, max_tokens=10, temperature=0.0)
        return "ANSWER" in response.upper()

    def process_special_message_types(self, user_input):
        """Process special message types like example requests."""
        if not user_input:
            return {"type": "regular_input"}
            
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
        """Get a simple example response using Claude - matching V3 behavior."""
        if not last_question:
            return "Unable to provide example - no question found."
            
        # Simplified approach matching V3
        messages = [
            {"role": "user", "content": f"Provide a brief example answer for this utility company question: {last_question}\n\nProvide ONLY the example text - no explanations, no HTML, no formatting. Just a simple example answer in 1-2 sentences."}
        ]

        try:
            example_response = self.get_response(messages, max_tokens=100, temperature=0.5)
            
            # Simple cleanup - remove any prefixes
            example_response = example_response.strip()
            prefixes = ["Example:", "Here's an example:", "For example:", "An example would be:"]
            for prefix in prefixes:
                if example_response.startswith(prefix):
                    example_response = example_response[len(prefix):].strip()
            
            return example_response if example_response else "We respond to emergency situations requiring immediate crew dispatch."
            
        except Exception as e:
            return "We respond to emergency situations requiring immediate crew dispatch."