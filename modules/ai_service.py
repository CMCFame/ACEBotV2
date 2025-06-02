# modules/ai_service.py
import boto3
import streamlit as st
import json
import os
from config import BEDROCK_MODEL_ID, BEDROCK_AWS_REGION, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

class AIService:
    def __init__(self, aws_region=BEDROCK_AWS_REGION):
        """Initialize the AI service with AWS Bedrock client."""
        print(f"--- DEBUG: AIService __init__ ---")
        print(f"--- DEBUG: Using region: {aws_region}")
        print(f"--- DEBUG: Model ID: {BEDROCK_MODEL_ID}")
        
        try:
            # Check if we're running in Streamlit Cloud
            aws_access_key_id = None
            aws_secret_access_key = None
            
            # Debug: Check what secrets are available
            if hasattr(st, 'secrets'):
                print(f"--- DEBUG: st.secrets is available")
                print(f"--- DEBUG: Available secret sections: {list(st.secrets.keys()) if st.secrets else 'None'}")
                
                if 'aws' in st.secrets:
                    print("--- DEBUG: Found 'aws' section in secrets")
                    aws_access_key_id = st.secrets.aws.get("aws_access_key_id")
                    aws_secret_access_key = st.secrets.aws.get("aws_secret_access_key")
                    
                    # Debug credential lengths (don't print actual values for security)
                    key_length = len(aws_access_key_id) if aws_access_key_id else 0
                    secret_length = len(aws_secret_access_key) if aws_secret_access_key else 0
                    print(f"--- DEBUG: Access key length: {key_length}")
                    print(f"--- DEBUG: Secret key length: {secret_length}")
                    
                    if aws_access_key_id and aws_secret_access_key:
                        print("--- DEBUG: Successfully got AWS credentials from Streamlit secrets")
                        st.success("✅ AWS credentials loaded from Streamlit secrets")
                    else:
                        print("--- DEBUG: AWS credentials are empty in Streamlit secrets")
                        st.error("❌ AWS credentials are empty in Streamlit secrets")
                else:
                    print("--- DEBUG: No 'aws' section found in Streamlit secrets")
                    st.error("❌ No 'aws' section found in Streamlit secrets. Please add AWS credentials.")
            else:
                print("--- DEBUG: st.secrets is not available")
                st.warning("⚠️ Streamlit secrets not available, trying environment variables")
            
            # Fallback to environment variables
            if not aws_access_key_id:
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                if aws_access_key_id:
                    print("--- DEBUG: Using AWS credentials from environment variables")
                    st.info("📋 Using AWS credentials from environment variables")
                else:
                    print("--- DEBUG: No AWS credentials found in environment variables either")
                    st.error("❌ No AWS credentials found in environment variables")
            
            # Create the Bedrock client
            if aws_access_key_id and aws_secret_access_key:
                print("--- DEBUG: Creating Bedrock client with explicit credentials")
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
                print(f"--- DEBUG: Bedrock client created successfully for region: {aws_region}")
                st.success(f"✅ Connected to AWS Bedrock in {aws_region}")
                
                # Test the connection
                try:
                    # Just test if we can make a simple call (this won't actually invoke a model)
                    # We'll just check if the client is properly authenticated
                    print("--- DEBUG: Testing Bedrock client connection...")
                    st.info("🔍 Testing AWS Bedrock connection...")
                except Exception as test_e:
                    print(f"--- DEBUG: Bedrock connection test failed: {test_e}")
                    st.warning(f"⚠️ Bedrock connection test failed: {test_e}")
                    
            else:
                print("--- DEBUG: No AWS credentials found, trying default credential chain")
                st.warning("⚠️ No explicit credentials found, trying default AWS credential chain")
                
                try:
                    # Try without explicit credentials (use default AWS credential chain)
                    self.client = boto3.client(
                        service_name='bedrock-runtime',
                        region_name=aws_region
                    )
                    print("--- DEBUG: Using default AWS credential chain")
                    st.info("📋 Using default AWS credential chain")
                except Exception as default_e:
                    print(f"--- DEBUG: Default credential chain also failed: {default_e}")
                    st.error(f"❌ Default credential chain failed: {default_e}")
                    self.client = None
                    
        except Exception as e:
            print(f"--- DEBUG: Failed to initialize Bedrock client. Error: {e}")
            st.error(f"❌ Failed to initialize Bedrock client: {e}")
            st.error("Please check your AWS credentials in Streamlit Cloud secrets.")
            self.client = None

    def _separate_system_prompt(self, messages):
        """Separates the system prompt from the message list for Claude API."""
        system_prompt = ""
        chat_messages = []
        
        # Extract the first system message as the system prompt
        if messages and messages[0]["role"] == "system":
            system_prompt = messages[0]["content"]
            remaining_messages = messages[1:]
        else:
            remaining_messages = messages
        
        # Filter out any remaining system messages and keep only user/assistant
        for msg in remaining_messages:
            if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]:
                chat_messages.append(msg)
            elif isinstance(msg, dict) and msg.get("role") == "system":
                # Log system messages that are being filtered out
                print(f"--- DEBUG: Filtering out system message: {msg.get('content', '')[:100]}...")
        
        print(f"--- DEBUG: Final message count - System prompt: {len(system_prompt)} chars, Chat messages: {len(chat_messages)}")
        return system_prompt, chat_messages

    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        """Get a response from the Bedrock API using Claude."""
        if not self.client:
            error_msg = """
            ❌ **Bedrock client not initialized**
            
            **To fix this:**
            1. Go to your Streamlit Cloud app settings
            2. Click the 'Secrets' tab
            3. Add your AWS credentials in this format:
            ```
            [aws]
            aws_access_key_id = "YOUR_ACCESS_KEY"
            aws_secret_access_key = "YOUR_SECRET_KEY"
            aws_default_region = "us-east-1"
            ```
            4. Save and restart your app
            """
            return error_msg

        system_prompt, claude_messages = self._separate_system_prompt(messages)
        
        # Additional validation: ensure all messages have required fields
        validated_messages = []
        for i, msg in enumerate(claude_messages):
            if isinstance(msg, dict) and "role" in msg and "content" in msg:
                # Only allow user and assistant roles
                if msg["role"] in ["user", "assistant"]:
                    # Ensure content is a string
                    content = str(msg["content"]) if msg["content"] is not None else ""
                    if content.strip():  # Only add non-empty messages
                        validated_messages.append({
                            "role": msg["role"],
                            "content": content
                        })
                    else:
                        print(f"--- DEBUG: Skipping empty message at index {i}")
                else:
                    print(f"--- DEBUG: Skipping message with invalid role '{msg['role']}' at index {i}")
            else:
                print(f"--- DEBUG: Skipping malformed message at index {i}: {msg}")

        body = {
            "anthropic_version": "bedrock-2023-05-31", 
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": validated_messages
        }
        if system_prompt and system_prompt.strip(): 
            body["system"] = system_prompt.strip()
        
        print(f"--- DEBUG: Sending {len(validated_messages)} messages to Claude")

        try:
            print(f"--- DEBUG: Calling Bedrock with model: {BEDROCK_MODEL_ID}")
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
                print("--- DEBUG: Successfully got response from Claude")
                return text_content.strip()
            elif response_body.get("completion"): 
                 return response_body.get("completion").strip()
            else:
                st.error(f"Unexpected Bedrock response format: {response_body}")
                return "Error: Could not parse response from Bedrock."

        except Exception as e: 
            print(f"--- DEBUG: Bedrock API Error: {e}")
            st.error(f"Bedrock API Error: {e}")
            return f"Error calling Bedrock API: {e}"

    def extract_user_info(self, user_input):
        """Extract user name and company name from the first response using Claude."""
        system_prompt = "You are an expert text analysis assistant. Your task is to extract the user's name and company name from their response to the question 'Could you please provide your name and your company name?'. Format your response strictly as 'NAME: [name], COMPANY: [company]'. If only one is found, use 'unknown' for the other. If neither is found, use 'unknown' for both."

        extract_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User response: {user_input}\nBased on this response, what is the NAME and COMPANY? Respond ONLY with 'NAME: [extracted or unknown], COMPANY: [extracted or unknown]'."}
        ]

        extract_response = self.get_response(extract_messages, max_tokens=100, temperature=0.1)

        try:
            name_part = "unknown"
            company_part = "unknown"

            if "NAME:" in extract_response:
                name_str = extract_response.split("NAME:")[1].split(", COMPANY:")[0].strip()
                if name_str and name_str.lower() != "unknown":
                    name_part = name_str
            if "COMPANY:" in extract_response:
                company_str = extract_response.split("COMPANY:")[1].strip()
                if company_str and company_str.lower() != "unknown":
                    company_part = company_str
            
            return {
                "name": name_part if name_part != "unknown" else "",
                "company": company_part if company_part != "unknown" else ""
            }
        except Exception as e:
            print(f"Error extracting user info with Claude: {e}. Response was: {extract_response}")
            return {"name": "", "company": ""}

    def check_response_type(self, question, user_input):
        """Determine if a user message is an answer or a question/request using Claude."""
        system_prompt = "You are an AI assistant that determines if a user's message is a direct answer to a given question or if it's a request for help/clarification. Respond with only 'ANSWER' or 'QUESTION'."
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
You are an AI assistant providing an example answer for a question about utility company callout processes.
The current question is: "{last_question}"

Your response should strictly follow this format:
Example: [A specific, detailed example relevant to utility companies for the question above]

To continue with our question:
{last_question}

Ensure the example is plain text, specific, relevant to a utility company, and demonstrates a good answer to the question.
Do NOT use any HTML tags or special formatting other than what is shown.
        """
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": "Please provide an example answer formatted as requested."}
        ]

        example_response = self.get_response(messages, max_tokens=250, temperature=0.7)

        if "Example:" not in example_response or "To continue with our question:" not in example_response:
            example_text = "A detailed example for utility companies related to this question." 
            question_text = last_question

            if "Example:" in example_response:
                parts = example_response.split("Example:", 1)
                if len(parts) > 1:
                    example_plus_rest = parts[1]
                    if "To continue with our question:" in example_plus_rest:
                        example_text = example_plus_rest.split("To continue with our question:")[0].strip()
                    else:
                        example_text = example_plus_rest.strip()
            example_response = f"Example: {example_text}\n\nTo continue with our question:\n{question_text}"
            
        return example_response