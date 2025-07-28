# simple_ace_app.py
"""
Complete ACE Questionnaire Bot - Simple, Reliable, Engaging
One file, all features, easy to maintain.
"""

import streamlit as st
import boto3
import json
import os
from datetime import datetime

# Configuration
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
BEDROCK_AWS_REGION = "us-east-1"

# Complete ACE Questions - Based on the original questionnaire
ACE_QUESTIONS = [
    # Basic Information
    {"id": 1, "text": "Could you please provide your name and company name?", "topic": "Basic Info", "tier": 1},
    {"id": 2, "text": "What type of situation are you responding to for this callout?", "topic": "Basic Info", "tier": 1},
    {"id": 3, "text": "How many employees are typically required for the callout?", "topic": "Staffing", "tier": 1},
    
    # Contact Process
    {"id": 4, "text": "Who do you call first and why?", "topic": "Contact Process", "tier": 1},
    {"id": 5, "text": "How many devices do they have?", "topic": "Contact Process", "tier": 1},
    {"id": 6, "text": "Which device do you call first and why?", "topic": "Contact Process", "tier": 1},
    {"id": 7, "text": "What types of devices are you calling?", "topic": "Contact Process", "tier": 1},
    
    # List Management
    {"id": 8, "text": "Is the next employee you call on the same list or a different list?", "topic": "List Management", "tier": 1},
    {"id": 9, "text": "How many lists (groups) total do you use for this callout?", "topic": "List Management", "tier": 1},
    {"id": 10, "text": "Are these lists based on job classification or some other attribute?", "topic": "List Management", "tier": 1},
    {"id": 11, "text": "How do you call this list - straight down or do you skip around?", "topic": "List Management", "tier": 1},
    {"id": 12, "text": "Do you skip around based on qualifications or employee status (vacation, sick, etc.)?", "topic": "List Management", "tier": 1},
    {"id": 13, "text": "Are there any pauses while calling this list?", "topic": "List Management", "tier": 1},
    
    # Insufficient Staffing
    {"id": 14, "text": "What happens when you don't get the required number of people?", "topic": "Insufficient Staffing", "tier": 1},
    {"id": 15, "text": "Do you call a different list or location? Is there any delay?", "topic": "Insufficient Staffing", "tier": 1},
    {"id": 16, "text": "Will you offer positions to someone you wouldn't normally call?", "topic": "Insufficient Staffing", "tier": 1},
    {"id": 17, "text": "Will you consider or call the whole list again?", "topic": "Insufficient Staffing", "tier": 1},
    {"id": 18, "text": "Do you always handle insufficient staffing the same way, or does it vary?", "topic": "Insufficient Staffing", "tier": 1},
    
    # Calling Logistics
    {"id": 19, "text": "Is there any issue with calling multiple employees simultaneously?", "topic": "Calling Logistics", "tier": 1},
    {"id": 20, "text": "Is there any issue with calling multiple devices simultaneously?", "topic": "Calling Logistics", "tier": 1},
    {"id": 21, "text": "Can someone say 'no, but call again if nobody else accepts'?", "topic": "Calling Logistics", "tier": 1},
    {"id": 22, "text": "If someone says no on the first pass, are they called on the second pass?", "topic": "Calling Logistics", "tier": 1},
    
    # List Changes (2nd Tier)
    {"id": 23, "text": "Do the order of the lists ever change over time?", "topic": "List Changes", "tier": 2},
    {"id": 24, "text": "When and how does the list order change?", "topic": "List Changes", "tier": 2},
    {"id": 25, "text": "Does the content of the lists (employees on them) ever change over time?", "topic": "List Changes", "tier": 2},
    {"id": 26, "text": "When and how does the list content change?", "topic": "List Changes", "tier": 2},
    
    # Tiebreakers
    {"id": 27, "text": "If you use overtime to order employees on lists, what are your tiebreakers?", "topic": "Tiebreakers", "tier": 2},
    {"id": 28, "text": "What is your first tiebreaker if two employees have the same overtime hours?", "topic": "Tiebreakers", "tier": 2},
    {"id": 29, "text": "What is your second tiebreaker?", "topic": "Tiebreakers", "tier": 2},
    {"id": 30, "text": "What is your third tiebreaker?", "topic": "Tiebreakers", "tier": 2},
    
    # Additional Rules (3rd Tier)
    {"id": 31, "text": "Would you ever email or text information to employees about the callout?", "topic": "Communication Rules", "tier": 3},
    {"id": 32, "text": "Do you have rules preventing callouts before/after normal working shifts?", "topic": "Communication Rules", "tier": 3},
    {"id": 33, "text": "Do you have rules that excuse declined callouts near shifts, vacations, or other schedule items?", "topic": "Communication Rules", "tier": 3},
]

class SimpleAIService:
    """Simple, reliable AI service focused on great conversations"""
    
    def __init__(self):
        self.client = self._init_bedrock_client()
    
    def _init_bedrock_client(self):
        """Initialize AWS Bedrock client with better error handling"""
        try:
            # Try Streamlit secrets first
            if hasattr(st, 'secrets') and 'aws' in st.secrets:
                aws_access_key_id = st.secrets.aws.get("aws_access_key_id")
                aws_secret_access_key = st.secrets.aws.get("aws_secret_access_key")
                print(f"DEBUG: Using Streamlit secrets")
            else:
                aws_access_key_id = os.getenv('AWS_ACCESS_KEY_ID')
                aws_secret_access_key = os.getenv('AWS_SECRET_ACCESS_KEY')
                print(f"DEBUG: Using environment variables")
            
            print(f"DEBUG: AWS Access Key ID: {aws_access_key_id[:10] if aws_access_key_id else 'None'}...")
            
            if aws_access_key_id and aws_secret_access_key:
                client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=BEDROCK_AWS_REGION,
                    aws_access_key_id=aws_access_key_id,
                    aws_secret_access_key=aws_secret_access_key
                )
                print(f"DEBUG: Bedrock client created successfully")
                
                # Test the connection with a simple API call
                try:
                    # Test with a minimal request to Claude
                    test_body = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": 10,
                        "messages": [{"role": "user", "content": "Hi"}]
                    }
                    
                    response = client.invoke_model(
                        modelId=BEDROCK_MODEL_ID,
                        contentType='application/json',
                        accept='application/json',
                        body=json.dumps(test_body)
                    )
                    print(f"DEBUG: Bedrock connection test successful")
                    return client
                except Exception as test_error:
                    print(f"DEBUG: Bedrock connection test failed: {test_error}")
                    st.error(f"❌ Cannot connect to AWS Bedrock: {test_error}")
                    
                    # Show specific fix instructions for AccessDeniedException
                    if "AccessDeniedException" in str(test_error):
                        st.warning("🔧 **AWS Permission Issue**: Your user needs Bedrock access permissions.")
                        st.code("""
Required AWS IAM Policy:
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel"
            ],
            "Resource": "arn:aws:bedrock:us-east-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
        }
    ]
}
                        """, language="json")
                        st.info("💡 Contact your AWS administrator to add this policy to your user account.")
                    else:
                        st.info("💡 Make sure your AWS account has access to Claude 3.5 Sonnet in the us-east-1 region")
                    return None
            else:
                print(f"DEBUG: Missing AWS credentials")
                st.error("❌ Missing AWS credentials")
                return None
                
        except Exception as e:
            print(f"DEBUG: Failed to initialize Bedrock client: {e}")
            st.error(f"❌ Failed to initialize AI service: {e}")
            return None
    
    def get_response(self, conversation_history, current_question_info):
        """Get engaging AI response for the current question"""
        if not self.client:
            # System unavailable - cannot proceed without AI
            return "❌ **System Unavailable** - The AI service is currently unavailable. Please contact your administrator to resolve the AWS Bedrock access issue."
        
        # Create engaging, focused system prompt
        system_prompt = f"""You are ACE, a friendly and professional AI assistant helping utility companies complete their ARCOS questionnaire. Your goal is to make this process engaging, efficient, and thorough.

CURRENT QUESTION: "{current_question_info['text']}"
Question ID: {current_question_info['id']}
Topic: {current_question_info['topic']} (Tier {current_question_info['tier']})
Progress: Question {current_question_info['id']} of {len(ACE_QUESTIONS)}

🚨 CRITICAL: You MUST follow the structured questionnaire exactly. 

CURRENT QUESTION TO ASK: "{current_question_info['text']}"

🚫 STRICT RULES:
- Ask ONLY the exact question shown above - nothing else
- NO additional questions, follow-ups, or clarifications in the same response
- NO multiple questions - one question per response ALWAYS
- DO NOT ask for examples, elaboration, or "anything else" in the same response

CONVERSATION GUIDELINES:
✅ Be conversational, encouraging, and professional
✅ Ask ONE question at a time and wait for the answer
✅ Provide gentle, natural guidance to help users give more complete answers
✅ If their answer seems vague, ask follow-up questions to get specifics
✅ Keep acknowledgments brief and varied - avoid repetitive phrasing
✅ Keep responses concise - aim for 1-2 sentences maximum

🚨 PRIVACY REQUIREMENTS:
❌ NEVER ask for or encourage full legal names, employee SSNs, addresses, phone numbers
❌ NEVER ask users to provide more personal information than what they initially offer
✅ Accept any name format they provide (first name, full name, etc.) - they saw the privacy notice
✅ Focus on processes and procedures, not personal details
✅ For question 1 (name/company): Don't provide examples - just accept whatever they give

ANSWER QUALITY GUIDANCE:
- Encourage specific details: "Could you tell me more about..." or "What specifically happens when..."
- Ask about the "why" behind processes: "What's the reason you do it that way?"
- Help them think through edge cases: "Are there any situations where this might be different?"
- Guide them toward complete answers without being pushy

EXAMPLES TO SHARE (when they ask "example", "help", or give vague answers):
- Contact Process: "We call the on-call dispatcher first because they coordinate the response and know current crew availability."
- List Management: "We have three lists: supervisors, lineworkers, and contractors, organized by seniority and overtime hours."
- Calling Logistics: "We can call multiple people simultaneously using our automated system, but union rules require specific notification order."
- Staffing: "We typically need 3-4 technicians for storm repairs, but only 1-2 for routine maintenance calls."
- Insufficient Staffing: "When we're short, we first call our backup list from the neighboring district, then contact contractors if needed."

HELP TRIGGERS - If they say any of these, provide an example and gentle guidance:
- "example", "help", "?", "what do you mean", "clarify", "explain", "I don't understand"
- Very short answers (1-3 words)
- Vague responses like "it depends", "various ways", "different methods"

Remember: You're helping them document their current processes clearly so ARCOS can be configured properly. Focus on understanding HOW they currently handle callouts with enough detail for technical implementation.

RESPONSE INSTRUCTIONS:
- If the user's answer is complete/acceptable: Give brief acknowledgment (or none), then ask the NEXT question in bold
- If their answer is too vague/short: Ask for clarification about the CURRENT question - do NOT advance to next question  
- If they're asking for help/examples: provide guidance but do NOT ask the next question yet - wait for their actual answer
- NEVER ask multiple questions in one response
- NEVER add "anything else?", "any other details?", or similar phrases
- Use **bold** formatting around question text for visibility

RESPONSE VARIATIONS - Use different acknowledgments:
- "Got it!" / "Perfect!" / "Thanks!" / "Understood."
- "That's helpful." / "Good to know." / "Clear."
- Just move directly to the next question without acknowledgment

EXAMPLE FORMATS (vary these):
"Got it! **[EXACT QUESTION TEXT FROM ABOVE]**"
"Perfect. **[EXACT QUESTION TEXT FROM ABOVE]**" 
"**[EXACT QUESTION TEXT FROM ABOVE]**"

IMPORTANT: Always wrap the question text in **bold** markdown for better visibility.

🚨 IMPORTANT: If the current question ID is 2 or higher, the user has already provided their name in a previous question. Do not ask for their name again."""
        
        try:
            # Prepare conversation for Claude - keep it focused on recent context
            messages = []
            recent_messages = conversation_history[-6:]  # Keep last 6 messages for context (3 exchanges)
            for msg in recent_messages:
                if msg["role"] in ["user", "assistant"]:
                    messages.append({"role": msg["role"], "content": msg["content"]})
            
            # API call to Claude
            body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": 800,
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
                return "I'm having trouble responding right now. Could you please try again?"
                
        except Exception as e:
            st.error(f"AI service error: {str(e)}")
            return "❌ **System Unavailable** - The AI service encountered an error. Please contact your administrator."
    

def init_session_state():
    """Initialize simple, reliable session state"""
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 1
    
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {"name": "", "company": "", "title": ""}
    
    if 'completed' not in st.session_state:
        st.session_state.completed = False
    
    if 'started' not in st.session_state:
        st.session_state.started = False

def get_current_question():
    """Get current question info"""
    current_num = st.session_state.current_question
    if current_num <= len(ACE_QUESTIONS):
        return ACE_QUESTIONS[current_num - 1]
    return None

def extract_user_info(user_input):
    """Simple extraction of user info from first response"""
    # Look for patterns like "John Smith - ABC Company" or "John from ABC"
    if " - " in user_input:
        parts = user_input.split(" - ")
        name = parts[0].strip()
        company = " - ".join(parts[1:]).strip()
        return name, company
    elif " from " in user_input.lower():
        parts = user_input.lower().split(" from ")
        name = parts[0].strip()
        company = " from ".join(parts[1:]).strip()
        return name, company
    elif " at " in user_input.lower():
        parts = user_input.lower().split(" at ")
        name = parts[0].strip()
        company = " at ".join(parts[1:]).strip()
        return name, company
    else:
        # Default: assume first word is name, rest is company
        words = user_input.strip().split()
        if len(words) >= 2:
            name = words[0]
            company = " ".join(words[1:])
            return name, company
    
    return user_input.strip(), ""

def display_progress():
    """Beautiful, encouraging progress display"""
    current = st.session_state.current_question
    total = len(ACE_QUESTIONS)
    progress = min((current - 1) / total, 1.0)  # -1 because we show progress after completing questions
    
    # Progress bar with custom styling
    st.markdown("""
        <style>
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #ff6b6b, #ee5a24, #ff9f43, #feca57);
        }
        </style>
    """, unsafe_allow_html=True)
    
    st.progress(progress)
    
    # Get current tier info
    current_q = get_current_question()
    tier_info = f"Tier {current_q['tier']}" if current_q else "Complete"
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Progress", f"{int(progress * 100)}%")
    with col2:
        st.metric("Question", f"{current-1}/{total}")
    with col3:
        st.metric("Current", tier_info)

def display_conversation():
    """Display conversation with better styling"""
    for message in st.session_state.conversation:
        if message["role"] == "user":
            with st.chat_message("user", avatar="👤"):
                st.write(message["content"])
        else:
            with st.chat_message("assistant", avatar="🤖"):
                st.write(message["content"])

def is_help_request(user_input, current_question_id=None):
    """Check if user is asking for help, examples, or giving vague answers that need guidance"""
    # Direct help requests
    help_keywords = ["example", "help", "?", "what do you mean", "clarify", "explain", "i don't understand", 
                     "show me", "can you give me", "not sure", "unclear", "confused"]
    
    # Vague responses that indicate they need guidance
    vague_responses = ["it depends", "various ways", "different methods", "not sure", "maybe", "sometimes", 
                       "varies", "different", "dunno", "idk", "i don't know"]
    
    user_lower = user_input.lower().strip()
    
    # Check for direct help requests
    if any(keyword in user_lower for keyword in help_keywords):
        return True
    
    # For Question 1 (name/company), don't treat short answers as help requests
    if current_question_id == 1:
        return False  # Name/company answers should always be accepted as-is
    
    # Check for very short answers (might need more detail) - but not for Question 1
    words = user_input.strip().split()
    if len(words) <= 2 and len(user_input.strip()) < 10:
        return True
        
    # Check for vague responses
    if any(vague in user_lower for vague in vague_responses):
        return True
    
    return False

def generate_summary():
    """Generate a clean summary of all answers"""
    if not st.session_state.answers:
        return "No responses recorded."
    
    summary = f"# ACE Questionnaire Summary\n"
    summary += f"**Participant:** {st.session_state.user_info.get('name', 'Unknown')}\n"
    summary += f"**Company:** {st.session_state.user_info.get('company', 'Unknown')}\n"
    summary += f"**Date:** {datetime.now().strftime('%B %d, %Y')}\n"
    summary += f"**Questions Completed:** {len(st.session_state.answers)}/{len(ACE_QUESTIONS)}\n\n"
    
    # Group by topic
    topics = {}
    for q_id, answer in st.session_state.answers.items():
        question = next((q for q in ACE_QUESTIONS if q["id"] == q_id), None)
        if question:
            topic = question["topic"]
            if topic not in topics:
                topics[topic] = []
            topics[topic].append({
                "question": question["text"],
                "answer": answer,
                "tier": question["tier"]
            })
    
    # Format by topic
    for topic, questions in topics.items():
        summary += f"## {topic}\n"
        for q in questions:
            summary += f"**Q:** {q['question']}\n"
            summary += f"**A:** {q['answer']}\n\n"
    
    return summary

def main():
    """Main application - simple and focused"""
    st.set_page_config(
        page_title="ACE Questionnaire Assistant",
        page_icon="🤖",
        layout="wide"
    )
    
    # Custom CSS for better styling
    st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 2rem 0;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-radius: 10px;
            margin-bottom: 2rem;
        }
        .stButton > button {
            background: linear-gradient(90deg, #ff6b6b, #ee5a24);
            color: white;
            border: none;
            border-radius: 20px;
            padding: 0.5rem 2rem;
            font-weight: bold;
        }
        .stButton > button:hover {
            background: linear-gradient(90deg, #ee5a24, #ff6b6b);
            border: none;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class="main-header">
            <h1>🤖 ACE Questionnaire Assistant</h1>
            <p>Making your ARCOS questionnaire easy, engaging, and efficient</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize
    init_session_state()
    ai_service = SimpleAIService()
    
    # Sidebar
    with st.sidebar:
        st.header("📊 Your Progress")
        display_progress()
        
        if st.session_state.user_info["name"]:
            st.success(f"👋 Hi {st.session_state.user_info['name']}!")
            if st.session_state.user_info["company"]:
                st.info(f"🏢 {st.session_state.user_info['company']}")
        
        st.markdown("---")
        st.subheader("🎯 Current Focus")
        current_q = get_current_question()
        if current_q:
            st.write(f"**Topic:** {current_q['topic']}")
            st.write(f"**Tier:** {current_q['tier']}")
            
            # Add contextual help hints
            st.markdown("---")
            st.subheader("💡 Answer Guidance")
            
            # Topic-specific guidance (skip for Basic Info name/company question)
            if current_q['id'] == 1:
                # Don't show guidance for name/company - they already saw privacy notice
                st.info("🎯 Just provide your name and company as you prefer - you've already seen our privacy guidelines.")
            else:
                topic_tips = {
                    "Basic Info": "Be specific about the types of situations and provide concrete details.",
                    "Staffing": "Mention specific numbers and types of employees (e.g., '3 lineworkers, 1 supervisor').",
                    "Contact Process": "Explain who you call and why - the reasoning helps configure the system properly.",
                    "List Management": "Describe how lists are organized (seniority, overtime, geography, etc.).",
                    "Insufficient Staffing": "Detail your backup procedures and any special rules for emergency situations.",
                    "Calling Logistics": "Mention any timing rules, simultaneous calling policies, or union requirements.",
                    "List Changes": "Explain how often and why lists change (monthly updates, overtime tracking, etc.).",
                    "Tiebreakers": "List tiebreakers in order of priority (1st: overtime, 2nd: seniority, etc.).",
                    "Communication Rules": "Include any restrictions on calling times, notification methods, or exemptions."
                }
                
                tip = topic_tips.get(current_q['topic'], "Be specific and explain the 'why' behind your processes.")
                st.info(f"🎯 {tip}")
            
            # Universal help reminder
            st.markdown("**Need help?** Just type 'example' or 'help' for guidance!")
        
        st.markdown("---")
        # Reset button
        if st.button("🔄 Start Over"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    
    # Main content area
    if st.session_state.completed:
        # Completion celebration
        st.balloons()
        st.success("🎉 **Congratulations!** You've completed the ACE questionnaire!")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
                ### 📋 Summary
                You've successfully answered **{len(st.session_state.answers)} questions** covering all aspects of your callout process. 
                This information will help configure ARCOS to match your current procedures perfectly.
            """)
        
        with col2:
            # Download summary
            summary_text = generate_summary()
            st.download_button(
                label="📥 Download Summary",
                data=summary_text,
                file_name=f"ACE_Summary_{st.session_state.user_info.get('company', 'Company')}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
        
        # Show detailed responses
        if st.expander("📖 View All Responses", expanded=False):
            st.markdown(summary_text)
            
    else:
        # Main conversation flow
        if not st.session_state.started:
            # Welcome screen
            st.markdown("""
                ### 👋 Welcome to the ACE Questionnaire!
                
                I'm here to help you document your utility company's callout processes for ARCOS implementation. 
                This should take about **15-20 minutes** and will help ensure ARCOS is configured perfectly for your needs.
                
                **What to expect:**
                - I'll ask you questions about how you currently handle callouts
                - Feel free to ask for examples if anything is unclear  
                - We'll go through this step-by-step at your pace
                
                ---
                
                **📋 Privacy Notice**
                
                ⚠️ **Do not include any personal identifying information (PII) or protected health information (PHI)** in your responses.
                
                - Use **company abbreviations** or generic names (e.g., "ABC Electric" instead of full legal names)  
                - **Avoid** SSNs, addresses, phone numbers, or other sensitive data
                
                This questionnaire focuses on **processes and procedures**, not personal information.
                
                ---
                
                Ready to get started?
            """)
            
            if st.button("🚀 Let's Begin!", type="primary"):
                st.session_state.started = True
                # Add welcome message to conversation
                welcome_msg = """Hi! I'm ACE, your questionnaire assistant. Let's start documenting your callout process. 

First, could you please provide your name and company name?"""
                
                st.session_state.conversation.append({"role": "assistant", "content": welcome_msg})
                st.rerun()
        
        else:
            # Show conversation
            display_conversation()
            
            # Get current question
            current_q = get_current_question()
            
            if current_q:
                # Chat input
                user_input = st.chat_input(f"💬 {current_q['text']}")
                
                if user_input:
                    # Store current question info before it gets changed
                    current_question_for_ai = current_q.copy()
                    
                    # Add user message to conversation
                    st.session_state.conversation.append({"role": "user", "content": user_input})
                    
                    # Extract user info from first question
                    if current_q["id"] == 1 and not st.session_state.user_info["name"]:
                        name, company = extract_user_info(user_input)
                        st.session_state.user_info["name"] = name
                        st.session_state.user_info["company"] = company
                    
                    # Get AI response using the stored question info
                    ai_response = ai_service.get_response(st.session_state.conversation, current_question_for_ai)
                    
                    # Check if system is unavailable
                    if "❌ **System Unavailable**" in ai_response:
                        # Don't progress, just show the error
                        st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                        st.error("**System Unavailable** - Please resolve the AWS Bedrock access issue to continue.")
                    else:
                        # System is working - proceed normally
                        # Check if this is a help request
                        if is_help_request(user_input, current_q["id"]):
                            # Just add the AI response for help - don't advance question
                            st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                        else:
                            # Check if AI is asking for clarification or accepting the answer
                            # If AI response contains the NEXT question, it means answer was accepted
                            next_question_text = ""
                            if st.session_state.current_question < len(ACE_QUESTIONS):
                                next_question_text = ACE_QUESTIONS[st.session_state.current_question]['text']
                            
                            # If AI response contains the next question text, answer was accepted
                            if next_question_text and next_question_text in ai_response:
                                # Answer accepted - store it and advance
                                st.session_state.answers[current_q["id"]] = user_input
                                st.session_state.current_question += 1
                                st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                            elif st.session_state.current_question >= len(ACE_QUESTIONS):
                                # Last question - check if it's a completion message
                                if "completes our questionnaire" in ai_response.lower() or "all" in ai_response.lower() and "questions completed" in ai_response.lower():
                                    st.session_state.answers[current_q["id"]] = user_input
                                    st.session_state.completed = True
                                    st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                                else:
                                    # Still asking for clarification on last question
                                    st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                            else:
                                # AI is asking for clarification - don't advance question
                                st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                    
                    st.rerun()

if __name__ == "__main__":
    main()