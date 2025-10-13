# simple_app.py
"""
Simplified ACE Questionnaire Bot - Focus on user experience over technical complexity
"""

import streamlit as st
import boto3
import json
import os
from datetime import datetime

# Simple configuration
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20241022-v2:0"
BEDROCK_AWS_REGION = "us-east-1"

# ACE Questions - Simple list instead of complex tracking
ACE_QUESTIONS = [
    {"id": 1, "text": "Could you please provide your name and company name?", "topic": "Basic Info"},
    {"id": 2, "text": "What type of situation are you responding to for this callout?", "topic": "Basic Info"},
    {"id": 3, "text": "How many employees are typically required for the callout?", "topic": "Staffing"},
    {"id": 4, "text": "Who do you call first and why?", "topic": "Contact Process"},
    {"id": 5, "text": "How many devices do they have?", "topic": "Contact Process"},
    {"id": 6, "text": "Which device do you call first and why?", "topic": "Contact Process"},
    {"id": 7, "text": "What types of devices are you calling?", "topic": "Contact Process"},
    {"id": 8, "text": "Is the next employee you call on the same list or a different list?", "topic": "List Management"},
    {"id": 9, "text": "How many lists total do you use for this callout?", "topic": "List Management"},
    {"id": 10, "text": "Are these lists based on job classification or other attributes?", "topic": "List Management"},
    # Add more questions as needed...
]

class SimpleAIService:
    """Simple AI service focused on conversation, not complex parsing"""
    
    def __init__(self):
        self.client = self._init_bedrock_client()
    
    def _init_bedrock_client(self):
        """Initialize AWS Bedrock client"""
        try:
            aws_access_key_id = st.secrets.get("aws", {}).get("aws_access_key_id") or os.getenv('AWS_ACCESS_KEY_ID')
            aws_secret_access_key = st.secrets.get("aws", {}).get("aws_secret_access_key") or os.getenv('AWS_SECRET_ACCESS_KEY')
            
            if aws_access_key_id and aws_secret_access_key:
                return boto3.client(
                    service_name='bedrock-runtime',
                    region_name=BEDROCK_AWS_REGION,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
            else:
                return boto3.client(service_name='bedrock-runtime', region_name=BEDROCK_AWS_REGION)
        except Exception as e:
            st.error(f"Failed to initialize AI service: {e}")
            return None
    
    def get_response(self, conversation_history, current_question_info):
        """Get AI response for the current question"""
        if not self.client:
            return "AI service is currently unavailable. Please try again later."
        
        # Simple system prompt focused on being helpful and engaging
        system_prompt = f"""You are a friendly, professional AI assistant helping utility companies complete the ACE questionnaire for ARCOS implementation.

Your current task: Guide the user through question {current_question_info['id']}: "{current_question_info['text']}"

Guidelines:
1. Be conversational, encouraging, and professional
2. If the user asks for an example, provide a brief, relevant one
3. If their answer seems incomplete, ask for clarification
4. Once they provide a good answer, acknowledge it and let them know you're moving to the next question
5. Keep responses concise and focused

Topic: {current_question_info['topic']}
Progress: Question {current_question_info['id']} of {len(ACE_QUESTIONS)}"""
        
        try:
            # Prepare messages for Claude
            messages = []
            for msg in conversation_history:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # Make API call
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 1000,
                "temperature": 0.7,
                "system": system_prompt,
                "messages": messages
            }
            
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
                return "I'm having trouble responding right now. Please try again."
                
        except Exception as e:
            st.error(f"AI service error: {str(e)}")
            return "I'm having trouble responding right now. Please try again."

def init_session_state():
    """Initialize simple session state"""
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 1
    
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {"name": "", "company": ""}
    
    if 'completed' not in st.session_state:
        st.session_state.completed = False

def get_current_question():
    """Get current question info"""
    current_num = st.session_state.current_question
    if current_num <= len(ACE_QUESTIONS):
        return ACE_QUESTIONS[current_num - 1]
    return None

def display_progress():
    """Simple progress display"""
    current = st.session_state.current_question
    total = len(ACE_QUESTIONS)
    progress = min(current / total, 1.0)
    
    st.progress(progress)
    st.caption(f"Question {current} of {total} • {int(progress * 100)}% Complete")

def display_conversation():
    """Display conversation history"""
    for message in st.session_state.conversation:
        if message["role"] == "user":
            with st.chat_message("user"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant"):
                st.write(message["content"])

def main():
    """Main application"""
    st.set_page_config(
        page_title="ACE Questionnaire Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    # Header
    st.title("🤖 ACE Questionnaire Assistant")
    st.subtitle("Let's make completing your ARCOS questionnaire easy and engaging!")
    
    # Initialize
    init_session_state()
    ai_service = SimpleAIService()
    
    # Sidebar with progress
    with st.sidebar:
        st.header("📊 Progress")
        display_progress()
        
        if st.session_state.user_info["name"]:
            st.success(f"👋 Hi {st.session_state.user_info['name']}!")
            st.info(f"🏢 Company: {st.session_state.user_info['company']}")
        
        # Reset button for testing
        if st.button("🔄 Start Over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main conversation area
    if st.session_state.completed:
        st.success("🎉 Congratulations! You've completed the ACE questionnaire!")
        st.balloons()
        
        # Show summary
        st.subheader("📋 Your Responses Summary")
        for q_id, answer in st.session_state.answers.items():
            question = next((q for q in ACE_QUESTIONS if q["id"] == q_id), None)
            if question:
                st.write(f"**{question['text']}**")
                st.write(f"→ {answer}")
                st.write("---")
    else:
        # Show conversation
        display_conversation()
        
        # Get current question
        current_q = get_current_question()
        
        if current_q:
            # Chat input
            user_input = st.chat_input(f"Your response to: {current_q['text']}")
            
            if user_input:
                # Add user message
                st.session_state.conversation.append({"role": "user", "content": user_input})
                
                # Extract user info from first question
                if current_q["id"] == 1 and not st.session_state.user_info["name"]:
                    # Simple parsing for name and company
                    parts = user_input.split("-")
                    if len(parts) >= 2:
                        st.session_state.user_info["name"] = parts[0].strip()
                        st.session_state.user_info["company"] = parts[1].strip()
                
                # Get AI response
                ai_response = ai_service.get_response(st.session_state.conversation, current_q)
                
                # Add AI message
                st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                
                # Simple logic to detect when to move to next question
                # For now, assume every user input is an attempt to answer
                if not user_input.lower().startswith(("example", "help", "?", "what do you mean")):
                    # Store the answer
                    st.session_state.answers[current_q["id"]] = user_input
                    
                    # Move to next question
                    if st.session_state.current_question < len(ACE_QUESTIONS):
                        st.session_state.current_question += 1
                    else:
                        st.session_state.completed = True
                
                st.rerun()
        
        # Show current question if no conversation yet
        if not st.session_state.conversation and current_q:
            welcome_msg = f"""👋 Welcome! I'm here to help you complete the ACE questionnaire for your ARCOS implementation. 

Let's start with question 1: **{current_q['text']}**

*Feel free to ask for examples if you need clarification!*"""
            
            st.session_state.conversation.append({"role": "assistant", "content": welcome_msg})
            st.rerun()

if __name__ == "__main__":
    main()