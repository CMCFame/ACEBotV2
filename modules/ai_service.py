# modules/ai_service.py
import openai
import streamlit as st
from config import OPENAI_MODEL, DEFAULT_MAX_TOKENS, DEFAULT_TEMPERATURE

class AIService:
    def __init__(self, api_key=None):
        """Initialize the OpenAI client."""
        if api_key:
            self.client = openai.OpenAI(api_key=api_key)
        else:
            # Try to get from secrets
            try:
                self.client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
            except Exception as e:
                st.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
    
    def get_response(self, messages, max_tokens=DEFAULT_MAX_TOKENS, temperature=DEFAULT_TEMPERATURE):
        """Get a response from the OpenAI API."""
        if not self.client:
            return "Error: OpenAI client not initialized"
            
        try:
            response = self.client.chat.completions.create(
                model=OPENAI_MODEL,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except openai.APIError as e:
            return f"Error: {e}"
    
    def extract_user_info(self, user_input):
        """Extract user name and company name from the first response."""
        # Special function to extract name and company from the first user message
        extract_messages = [
            {"role": "system", "content": "Extract the user name and company name from this response to the question 'Could you please provide your name and your company name?'. Even if the response is brief or partial, try to identify name and company information."},
            {"role": "user", "content": f"User response: {user_input}\nExtract only the name and company. Format your response exactly as: NAME: [name], COMPANY: [company]. If you can only extract one of these, still provide it and use 'unknown' for the other."}
        ]
        
        extract_response = self.get_response(extract_messages, max_tokens=100)
        
        try:
            # Parse the extraction response
            name_part = "unknown"
            company_part = "unknown"
            
            if "NAME:" in extract_response:
                name_part = extract_response.split("NAME:")[1].split(",")[0].strip()
                name_part = name_part.replace("[", "").replace("]", "")
                
            if "COMPANY:" in extract_response:
                company_part = extract_response.split("COMPANY:")[1].strip()
                company_part = company_part.replace("[", "").replace("]", "")
            
            return {
                "name": name_part if name_part != "unknown" else "",
                "company": company_part if company_part != "unknown" else ""
            }
        except Exception as e:
            print(f"Error extracting user info: {e}")
            return {"name": "", "company": ""}
    
    def check_response_type(self, question, user_input):
        """Determine if a user message is an answer or a question/request."""
        messages = [
            {"role": "system", "content": "You are helping to determine if a user message is an answer to a question or a request for help/clarification."},
            {"role": "user", "content": f"Question: {question}\nUser message: {user_input}\nIs this a direct answer to the question or a request for help/clarification? Reply with exactly 'ANSWER' or 'QUESTION'."}
        ]
        
        response = self.get_response(messages, max_tokens=50, temperature=0.1)
        return "ANSWER" in response.upper()
    
    def process_special_message_types(self, user_input):
        """Process special message types like example requests."""
        lower_input = user_input.lower().strip()
        
        # Check for example requests
        if lower_input in ["example", "show example", "give me an example", "example answer", "can you show me an example?"]:
            return {"type": "example_request"}
        
        # Check for help requests
        if lower_input in ["?", "help", "i need help", "what do you mean"]:
            return {"type": "help_request"}
            
        # Check for summary requests
        if lower_input in ["summary", "download", "download summary", "get summary", "show summary", "yes", "provide summary"]:
            return {"type": "summary_request"}
            
        # Check for frustration indicators
        if any(phrase in lower_input for phrase in ["already answered", "not helpful", "i already responded", "already responded"]):
            return {"type": "frustration", "subtype": "summary_request"}
            
        # Default - regular input
        return {"type": "regular_input"}
        
    def get_example_response(self, last_question):
        """Get a consistently formatted example response with plain text formatting."""
        # Modified system message to generate plain text format without HTML
        system_message = """
        You are providing an example answer to a question about utility company callout processes.
        
        Format your response exactly as follows:
        
        Example: [Your specific, detailed example relevant to utility companies]
        
        To continue with our question:
        [Repeat or rephrase the original question]
        
        Do NOT use any HTML tags or special formatting in your response. Use only plain text.
        The example should be specific, relevant to a utility company, and demonstrate a good answer.
        """
        
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Provide an example answer for this question: {last_question}"}
        ]
        
        example_response = self.get_response(messages, max_tokens=250, temperature=0.7)
        
        # Simple validation
        if "Example:" not in example_response:
            example_response = f"Example: A detailed example for utility companies related to this question.\n\nTo continue with our question:\n{last_question}"
            
        if "To continue with our question:" not in example_response:
            parts = example_response.split("\n\n")
            if len(parts) > 0:
                example_part = parts[0]
                example_response = f"{example_part}\n\nTo continue with our question:\n{last_question}"
        
        return example_response