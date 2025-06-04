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
        """Clean messages and prepare them for Claude, consolidating all system prompts into one string."""
        consolidated_system_prompt = ""
        claude_messages = []

        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
                
            role = msg["role"]
            content = str(msg["content"]) if msg["content"] is not None else ""
            
            if role == "system":
                # Consolidate all system messages into one system prompt string
                consolidated_system_prompt += content.strip() + "\n\n"
            elif role in ["user", "assistant"] and content.strip():
                claude_messages.append({"role": role, "content": content.strip()})
        
        return consolidated_system_prompt.strip(), claude_messages

    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        """Get a response from the Bedrock API using Claude."""
        if not self.client:
            return "Bedrock client not initialized. Please check AWS credentials configuration."

        try:
            system_prompt, claude_messages = self._clean_and_prepare_messages(messages)
            
            # Ensure we have at least one message for Claude
            if not claude_messages:
                # If there are no user/assistant messages but there is a system prompt,
                # create a dummy user message to initiate the conversation from the system prompt.
                # This is crucial if the AI needs to start by asking a question after a system instruction.
                if system_prompt:
                     # Check if the last message in the original `messages` list was a system message
                     # that might imply the AI should now speak.
                    if messages and messages[-1].get("role") == "system":
                        # This indicates the AI should respond to system instructions, e.g., ask a question.
                        # A neutral prompt to get the AI to act based on its system instructions.
                         pass # No dummy message needed if system_prompt is present, AI should act on it.
                    else:
                        # This case should ideally not be hit if chat_history always has user/assistant turns.
                        return "No valid conversational messages to process, and system prompt does not seem to be the last directive."
                else:
                    return "No valid messages or system prompt to process."


            body = {
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": claude_messages # Claude messages should not be empty here
            }
            
            # Add system prompt if available and non-empty
            if system_prompt: # No need for .strip() here as it was stripped during consolidation
                body["system"] = system_prompt

            # Safety check: if claude_messages is empty but we have a system_prompt,
            # we might need a way to make Claude "speak first" based on system instructions.
            # However, Claude's message API typically expects at least one user message.
            # The current app structure (user input -> AI response) means claude_messages will usually not be empty
            # once a conversation starts. For the very first message, app.py provides a welcome message.
            if not claude_messages and not system_prompt: # Defensive check
                 return "Error: No messages and no system prompt to send to Bedrock."
            if not claude_messages and system_prompt and not (messages and messages[-1].get("role") == "system"):
                 # This case is tricky. If only a system prompt exists and no conversational history,
                 # Claude might not respond. The application flow should ensure this doesn't happen
                 # without a clear "instruction" for Claude to start.
                 # For now, we'll rely on the existing app.py logic which always has some history.
                 # If problems persist where AI doesn't start, a specific initial user message like "Proceed." might be needed.
                 # For robustness, if claude_messages is empty but there's a system_prompt,
                 # let's add a neutral starting message if the last actual message wasn't system.
                 # This helps if system messages were the *only* thing in history.
                 # However, `_clean_and_prepare_messages` already filters out system messages into `system_prompt`.
                 # This implies `claude_messages` would be empty if the original `messages` only contained system roles.
                 # The Bedrock API expects at least one message in the "messages" array.
                 # If `claude_messages` is empty, and there's a `system_prompt`,
                 # it means the AI is expected to "speak first" based on the system prompt.
                 # We can send a "dummy" user message that just prompts it to act.
                 # This part of the logic might need further refinement based on how Claude behaves
                 # when `messages` is empty but `system` is populated.
                 # For now, the existing check in get_response handles empty claude_messages by creating a dummy message.
                 pass


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
            elif response_body.get("completion"): # Older Claude models might use this
                return response_body.get("completion").strip()
            else:
                # Log the actual error or response for debugging
                # print(f"Unexpected response structure from Bedrock: {response_body}")
                return "Error: Could not parse response from Bedrock."

        except Exception as e: 
            # print(f"Error in get_response: {e}")
            # st.error(f"Bedrock API Error: {e}") # Optional: display error in UI
            return f"Error calling Bedrock API: {str(e)}"

    def extract_user_info(self, user_input):
        """Extract user name and company name from the first response using Claude."""
        system_prompt = (
            "You are an expert text analysis assistant. Your task is to extract the user's name and company name "
            "from their response to the question 'Could you please provide your name and your company name?'.\n\n"
            "Respond ONLY with the following exact format:\n"
            "NAME: [extracted name or unknown], COMPANY: [extracted company or unknown]\n\n"
            "Do not include any other text, greetings, or explanations. Only the 'NAME: ..., COMPANY: ...' line."
        )

        # Construct messages for this specific task
        # The system prompt is passed separately for Claude
        messages_for_extraction = [
            {"role": "system", "content": system_prompt}, # This will be handled by _clean_and_prepare_messages
            {"role": "user", "content": f"User response: {user_input}"}
        ]

        extract_response = self.get_response(messages_for_extraction, max_tokens=100, temperature=0.0)


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
                # Determine end of name string: either before ", COMPANY:" or end of string
                name_end_index = -1
                if company_start_index != -1 and company_start_index > name_value_start:
                    # Check for a comma before COMPANY if on the same line
                    comma_before_company = raw_response_str.rfind(",", name_value_start, company_start_index)
                    if comma_before_company != -1:
                        name_end_index = comma_before_company
                    else:
                        name_end_index = company_start_index # No comma, name ends where company starts
                
                if name_end_index != -1:
                    name_str_candidate = raw_response_str[name_value_start:name_end_index].strip()
                else: # No COMPANY marker after NAME, or malformed
                    name_str_candidate = raw_response_str[name_value_start:].split("\n")[0].strip() # Take up to newline


                if name_str_candidate and name_str_candidate.lower() != "unknown":
                    name_part = name_str_candidate.replace("[", "").replace("]", "").strip()


            if company_start_index != -1:
                company_value_start = company_start_index + len(company_marker)
                company_str_candidate = raw_response_str[company_value_start:].split("\n")[0].strip() # Take up to newline

                if company_str_candidate and company_str_candidate.lower() != "unknown":
                    company_part = company_str_candidate.replace("[", "").replace("]", "").strip()
            
            return {
                "name": name_part if name_part and name_part.lower() != "unknown" else "",
                "company": company_part if company_part and company_part.lower() != "unknown" else ""
            }
        except Exception as e:
            print(f"Error extracting user info with Claude: {e}. Response was: {extract_response}")
            return {"name": "", "company": ""}

    def check_response_type(self, question, user_input):
        """Determine if a user message is an answer or a question/request using Claude."""
        system_prompt = "You are an AI assistant that determines if a user's message is a direct answer to a given question or if it's a request for help or clarification. Respond with only the single word 'ANSWER' or the single word 'QUESTION'."
        
        messages_for_check = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The question asked was: '{question}'. The user responded: '{user_input}'. Is the user's response a direct answer to the question, or is it a request for help or clarification? Respond with only the single word 'ANSWER' or 'QUESTION'."}
        ]

        response = self.get_response(messages_for_check, max_tokens=10, temperature=0.0)
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
        
        messages_for_example = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": "Provide the example answer now."}
        ]

        example_response_text = self.get_response(messages_for_example, max_tokens=150, temperature=0.7) # Increased max_tokens slightly
        return example_response_text.strip()