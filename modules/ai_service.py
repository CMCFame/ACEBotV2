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
            aws_access_key_id = None
            aws_secret_access_key = None
            
            if hasattr(st, 'secrets'):
                print(f"--- DEBUG: st.secrets is available")
                if 'aws' in st.secrets:
                    print("--- DEBUG: Found 'aws' section in secrets")
                    aws_access_key_id = st.secrets.aws.get("aws_access_key_id")
                    aws_secret_access_key = st.secrets.aws.get("aws_secret_access_key")
                    if aws_access_key_id and aws_secret_access_key:
                        print("--- DEBUG: Successfully got AWS credentials from Streamlit secrets")
                    else:
                        print("--- DEBUG: AWS credentials are empty in Streamlit secrets")
                else:
                    print("--- DEBUG: No 'aws' section found in Streamlit secrets")
            else:
                print("--- DEBUG: st.secrets is not available, trying environment variables")
            
            if not aws_access_key_id: # Fallback to environment variables
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                if aws_access_key_id:
                    print("--- DEBUG: Using AWS credentials from environment variables")

            if aws_access_key_id and aws_secret_access_key:
                print("--- DEBUG: Creating Bedrock client with explicit credentials")
                self.client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=aws_region,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
                print(f"--- DEBUG: Bedrock client created successfully for region: {aws_region}")
            else:
                print("--- DEBUG: No AWS credentials found, trying default credential chain")
                try:
                    self.client = boto3.client(service_name='bedrock-runtime', region_name=aws_region)
                    print("--- DEBUG: Using default AWS credential chain")
                except Exception as default_e:
                    print(f"--- DEBUG: Default credential chain also failed: {default_e}")
                    self.client = None
                    st.error(f"❌ Default AWS credential chain failed: {default_e}. Ensure your AWS environment is configured or provide credentials in Streamlit secrets.")
                    
        except Exception as e:
            print(f"--- DEBUG: Failed to initialize Bedrock client. Error: {e}")
            st.error(f"❌ Failed to initialize Bedrock client: {e}. Check AWS credentials.")
            self.client = None

    def _separate_system_prompt(self, messages):
        """Separates the system prompt from the message list for Claude API."""
        system_prompt = ""
        chat_messages = []
        
        if messages and messages[0]["role"] == "system":
            system_prompt = messages[0]["content"]
            remaining_messages = messages[1:]
        else:
            remaining_messages = messages
        
        for msg in remaining_messages:
            if isinstance(msg, dict) and msg.get("role") in ["user", "assistant"]:
                chat_messages.append(msg)
            elif isinstance(msg, dict) and msg.get("role") == "system":
                # This system message will be ignored by Claude if a main one is already provided.
                # It's better to change its role to "user" and mark it as an instruction if it's turn-specific.
                print(f"--- DEBUG: Filtering out subsequent system message: {msg.get('content', '')[:100]}...")
        
        return system_prompt, chat_messages

    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        """Get a response from the Bedrock API using Claude."""
        if not self.client:
            error_msg = "Bedrock client not initialized. Please check AWS credentials configuration."
            return error_msg

        print(f"--- DEBUG: get_response called with {len(messages)} messages")
        
        try:
            system_prompt, claude_messages = self._separate_system_prompt(messages)
            
            validated_messages = []
            for i, msg in enumerate(claude_messages):
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    if msg["role"] in ["user", "assistant"]:
                        content = str(msg["content"]) if msg["content"] is not None else ""
                        if content.strip():
                            validated_messages.append({"role": msg["role"], "content": content})
                        else: print(f"--- DEBUG: Skipping empty message at index {i}")
                    else: print(f"--- DEBUG: Skipping message with invalid role '{msg['role']}' at index {i}")
                else: print(f"--- DEBUG: Skipping malformed message at index {i}: {type(msg)}")

            if not validated_messages and not system_prompt.strip(): # Allow if only system prompt exists
                 # If only system prompt exists and no user/assistant messages, it's unusual for a turn.
                 # However, if there's a system prompt, we might still proceed if claude_messages is empty (e.g. first turn after system).
                 # But if validated_messages is empty (meaning all user/assistant messages were filtered), and there's NO system prompt, that's an issue.
                 # If Claude needs at least one message in the "messages" array:
                if not validated_messages:
                    print("--- DEBUG: No valid user/assistant messages found, and Claude requires at least one. Returning error.")
                    return "I'm having trouble processing the conversation. Please try rephrasing your message or ensure context is not empty."


            body = {
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": validated_messages # This can be empty if only a system prompt is provided and it's the first interaction
            }
            if system_prompt and system_prompt.strip(): 
                body["system"] = system_prompt.strip()
                print(f"--- DEBUG: Added system prompt with {len(system_prompt)} characters")
            
            # Ensure body["messages"] is not empty if that's a strict API requirement for Claude when system prompt is also present
            if not body["messages"] and "system" not in body: # If no system prompt AND no messages, it's an error
                return "Cannot send an empty request to the AI."
            if not body["messages"] and body.get("system"): # If system prompt IS there, but messages is empty
                 # Claude might allow a system prompt and then the first "user" turn is implied to be an empty input to kick off.
                 # Or, it might require at least one message in the messages list. Let's assume it needs one if system is present.
                 # This case should be rare with the current app flow.
                 print(f"--- DEBUG: Sending request with system prompt but empty 'messages' list. This might be okay for Claude's first turn after system prompt.")


            print(f"--- DEBUG: Sending request to Bedrock. System prompt present: {'system' in body}. Messages count: {len(validated_messages)}")

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
                print(f"--- DEBUG: Successfully got response from Claude: {len(text_content)} characters")
                return text_content.strip()
            elif response_body.get("completion"): # Older Claude versions might use this
                 return response_body.get("completion").strip()
            else:
                print(f"--- DEBUG: Unexpected response format: {response_body}")
                return "Error: Could not parse response from Bedrock."

        except Exception as e: 
            print(f"--- DEBUG: Exception in get_response: {e}")
            import traceback
            print(f"--- DEBUG: Full traceback: {traceback.format_exc()}")
            return f"Error calling Bedrock API: {e}"

    def extract_user_info(self, user_input):
        """Extract user name and company name from the first response using Claude."""
        # *** MODIFIED SECTION FOR EXTRACT_USER_INFO PROMPT START ***
        system_prompt = (
            "You are an expert text analysis assistant. Your task is to extract the user's name and company name "
            "from their response to the question 'Could you please provide your name and your company name?'.\n\n"
            "Respond ONLY with the following exact format:\n"
            "NAME: [extracted name or unknown], COMPANY: [extracted company or unknown]\n\n"
            "Examples of your exact output (these are literal strings you should emulate):\n"
            "- If name is 'John Doe' and company is 'ACME Corp', respond: NAME: John Doe, COMPANY: ACME Corp\n"
            "- If only name 'Jane' is found, respond: NAME: Jane, COMPANY: unknown\n"
            "- If only company 'Beta Inc.' is found, respond: NAME: unknown, COMPANY: Beta Inc.\n"
            "- If neither is found, respond: NAME: unknown, COMPANY: unknown\n\n"
            "Do not include any other text, greetings, or explanations. Only the 'NAME: ..., COMPANY: ...' line."
        )
        # *** MODIFIED SECTION FOR EXTRACT_USER_INFO PROMPT END ***

        extract_messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User response: {user_input}"}
        ]

        extract_response = self.get_response(extract_messages, max_tokens=100, temperature=0.0) # Low temp for precision

        try:
            name_part = "unknown"
            company_part = "unknown"

            # More robust parsing attempts
            raw_response_str = str(extract_response).strip()

            name_marker = "NAME:"
            company_marker = "COMPANY:"

            name_start_index = raw_response_str.find(name_marker)
            company_start_index = raw_response_str.find(company_marker)

            if name_start_index != -1:
                # Assumes "NAME: content, COMPANY: content" or "NAME: content"
                name_value_start = name_start_index + len(name_marker)
                if company_start_index != -1 and company_start_index > name_start_index:
                    # NAME is before COMPANY
                    name_str_candidate = raw_response_str[name_value_start:company_start_index].replace(",", "").strip()
                else:
                    # NAME is present, COMPANY might not be or is handled separately
                    name_str_candidate = raw_response_str[name_value_start:].strip()
                
                if name_str_candidate and name_str_candidate.lower() != "unknown":
                    name_part = name_str_candidate

            if company_start_index != -1:
                company_value_start = company_start_index + len(company_marker)
                # Assumes "COMPANY: content" possibly at the end or before NAME if order is swapped
                # For simplicity, just takes rest of string after COMPANY marker if it exists
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
        return "ANSWER" in response.upper() # Simple check, assumes AI follows instruction

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
        """Get a consistently formatted example response using Claude. Returns ONLY the example text."""
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
            {"role": "user", "content": "Provide the example answer now."} # Simple trigger
        ]

        example_response_text = self.get_response(messages, max_tokens=100, temperature=0.7) # Increased tokens slightly for example
        
        # Minimal cleanup, as the prompt is now very direct.
        return example_response_text.strip()