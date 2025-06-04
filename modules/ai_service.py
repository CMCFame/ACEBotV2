# modules/ai_service.py
import boto3
import streamlit as st
import json
import os
from config import BEDROCK_MODEL_ID, BEDROCK_AWS_REGION, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

class AIService:
    def __init__(self, aws_region=BEDROCK_AWS_REGION):
        # ... (existing __init__ code)
        try:
            aws_access_key_id = st.secrets.aws.get("aws_access_key_id") if hasattr(st, 'secrets') and 'aws' in st.secrets else os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = st.secrets.aws.get("aws_secret_access_key") if hasattr(st, 'secrets') and 'aws' in st.secrets else os.getenv('AWS_SECRET_ACCESS_KEY')

            if aws_access_key_id and aws_secret_access_key:
                self.client = boto3.client(
                    service_name='bedrock-runtime', region_name=aws_region,
                    aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key
                )
            else: # Try default provider chain
                self.client = boto3.client(service_name='bedrock-runtime', region_name=aws_region)
        except Exception as e:
            st.error(f"❌ Failed to initialize Bedrock client: {e}. Ensure AWS credentials and region are correctly configured.")
            self.client = None


    def _clean_and_prepare_messages(self, messages):
        consolidated_system_prompt = ""
        claude_messages = []
        for msg in messages:
            if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                continue
            role = msg["role"]
            content = str(msg["content"]) if msg["content"] is not None else ""
            
            if role == "system":
                consolidated_system_prompt += content.strip() + "\n\n"
            elif role in ["user", "assistant"] and (content.strip() or role == "user"): # Keep user message even if "empty" for initial trigger
                claude_messages.append({"role": role, "content": content.strip()})
        return consolidated_system_prompt.strip(), claude_messages

    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        if not self.client:
            return "Bedrock client not initialized. Please check AWS credentials configuration."

        try:
            system_prompt, claude_messages = self._clean_and_prepare_messages(messages)
            
            api_call_messages = []

            if system_prompt:
                if not claude_messages: # AI's first turn, only system prompt was provided
                    # Claude API: "If you include a system prompt, the messages array must start with a user turn."
                    # The system prompt has instructions for the AI on how to begin.
                    api_call_messages = [{"role": "user", "content": "Please proceed based on your instructions."}]
                elif claude_messages[0]["role"] == "assistant":
                    # History started with system, then assistant (e.g. from a hardcoded first message)
                    # Prepend a dummy user message to make the sequence: user, assistant, user...
                    # This is a safeguard; ideally, app.py structure should avoid this for Claude.
                    api_call_messages = [{"role": "user", "content": "Context."}] 
                    api_call_messages.extend(claude_messages)
                    # st.warning("AIService: Adjusted message order for Claude API compliance.") # Optional debug
                else: # History is fine (starts with user, or no system prompt and starts with user)
                    api_call_messages = claude_messages
            else: # No system prompt
                api_call_messages = claude_messages

            if not api_call_messages and not system_prompt: # Nothing to send
                 return "Error: No messages or system prompt to process."
            # If system_prompt is present, api_call_messages is guaranteed to be non-empty here.
            # If no system_prompt, api_call_messages could be empty if original messages was empty.
            if not api_call_messages and system_prompt : #This case should be covered above
                 return "Error: System prompt present but no messages for API call."


            body = {
                "anthropic_version": "bedrock-2023-05-31", 
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": api_call_messages
            }
            
            if system_prompt:
                body["system"] = system_prompt
            
            # Make sure messages array is not empty if we are sending it
            if not body["messages"] and "system" not in body: # Final safety if somehow messages became empty and no system prompt
                 return "Error: No content to send to Bedrock model."
            if not body["messages"] and "system" in body and not body["system"]: # System prompt is empty string
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
                # Fallback for unexpected structure
                st.warning(f"Unexpected response structure from Bedrock: {response_body}")
                return "Error: Could not parse response from Bedrock."

        except Exception as e: 
            st.error(f"Bedrock API Call Error: {str(e)}")
            return f"Error calling Bedrock API: {str(e)}"

    def extract_user_info(self, user_input):
        # ... (existing extract_user_info code, should still work)
        system_prompt = (
            "You are an expert text analysis assistant. Your task is to extract the user's name and company name "
            "from their response to the question 'Could you please provide your name and your company name?'.\n\n"
            "Respond ONLY with the following exact format:\n"
            "NAME: [extracted name or unknown], COMPANY: [extracted company or unknown]\n\n"
            "Do not include any other text, greetings, or explanations. Only the 'NAME: ..., COMPANY: ...' line."
        )
        messages_for_extraction = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"User response: {user_input}"}
        ]
        extract_response = self.get_response(messages_for_extraction, max_tokens=100, temperature=0.0)
        try:
            name_part = "unknown"; company_part = "unknown"
            raw_response_str = str(extract_response).strip()
            name_marker = "NAME:"; company_marker = "COMPANY:"
            name_start_index = raw_response_str.find(name_marker)
            company_start_index = raw_response_str.find(company_marker)
            if name_start_index != -1:
                name_value_start = name_start_index + len(name_marker)
                name_end_index = company_start_index if company_start_index > name_value_start else len(raw_response_str)
                name_str_candidate = raw_response_str[name_value_start:name_end_index].split("\n")[0].replace(",", "").strip()
                if name_str_candidate and name_str_candidate.lower() != "unknown": name_part = name_str_candidate.replace("[", "").replace("]", "").strip()
            if company_start_index != -1:
                company_value_start = company_start_index + len(company_marker)
                company_str_candidate = raw_response_str[company_value_start:].split("\n")[0].strip()
                if company_str_candidate and company_str_candidate.lower() != "unknown": company_part = company_str_candidate.replace("[", "").replace("]", "").strip()
            return {"name": name_part if name_part and name_part.lower() != "unknown" else "", "company": company_part if company_part and company_part.lower() != "unknown" else ""}
        except Exception as e:
            print(f"Error extracting user info with Claude: {e}. Response was: {extract_response}")
            return {"name": "", "company": ""}


    def check_response_type(self, question, user_input):
        # ... (existing check_response_type code, should still work)
        system_prompt = "You are an AI assistant that determines if a user's message is a direct answer to a given question or if it's a request for help or clarification. Respond with only the single word 'ANSWER' or the single word 'QUESTION'."
        messages_for_check = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"The question asked was: '{question}'. The user responded: '{user_input}'. Is the user's response a direct answer to the question, or is it a request for help or clarification? Respond with only the single word 'ANSWER' or 'QUESTION'."}
        ]
        response = self.get_response(messages_for_check, max_tokens=10, temperature=0.0)
        return "ANSWER" in response.upper() if response else False


    def process_special_message_types(self, user_input):
        # ... (existing process_special_message_types code)
        lower_input = user_input.lower().strip()
        if lower_input in ["example", "show example", "give me an example", "example answer", "can you show me an example?"]: return {"type": "example_request"}
        if lower_input in ["?", "help", "i need help", "what do you mean"]: return {"type": "help_request"}
        if lower_input in ["summary", "download", "download summary", "get summary", "show summary", "yes", "provide summary"]: return {"type": "summary_request"}
        if any(phrase in lower_input for phrase in ["already answered", "not helpful", "i already responded", "already responded"]): return {"type": "frustration", "subtype": "summary_request"}
        return {"type": "regular_input"}

    def get_example_response(self, last_question):
        # ... (existing get_example_response code, ensure it's robust)
        system_message = f"""
You are providing a brief example answer for a utility company callout process question.
The question you need to provide an example for is: "{last_question}"
Your task is to provide ONLY the example text itself. It should be short (1-2 sentences) and specific.
Do NOT include any prefixes like "Example:", "Here's an example:", or any explanations.
Do NOT repeat the question. Just output the example sentence(s).
For instance, if the question was about who to contact first, a good direct example output from you would be:
"We contact the on-call supervisor first as they are responsible for assessing the situation and dispatching the appropriate crew."
"""
        messages_for_example = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": "Provide the example answer now."}
        ]
        example_response_text = self.get_response(messages_for_example, max_tokens=150, temperature=0.7)
        return example_response_text.strip() if example_response_text else "Could not generate an example at this time."