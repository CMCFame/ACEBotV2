# simple_ace_app.py
"""
Complete ACE Questionnaire Bot - Simple, Reliable, Engaging
One file, all features, easy to maintain.
"""

import streamlit as st
import boto3
import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime

# Configuration
BEDROCK_MODEL_ID = "anthropic.claude-3-5-sonnet-20240620-v1:0"
BEDROCK_AWS_REGION = "us-east-1"

# Complete ACE Questions - Reframed for conciseness and clarity
ACE_QUESTIONS = [
    # Section 1: Basic Callout Information
    {"id": 1, "text": "Describe the type of situation or event that triggers this callout process.", "topic": "Basic Information", "tier": 1},
    {"id": 2, "text": "How many employees, and with which roles or job classifications, are typically required for this type of event?", "topic": "Basic Information", "tier": 1},
    
    # Section 2: Initial Contact Process
    {"id": 3, "text": "Who is contacted first, and what is the main reason for that person or role being the first?", "topic": "Contact Process", "tier": 1},
    {"id": 4, "text": "Thinking of the first person to be contacted, how many devices are used to try and reach them (e.g., work phone, personal cell)?", "topic": "Contact Process", "tier": 1},
    {"id": 5, "text": "Are those devices contacted one by one in a specific order, or all at the same time? If in order, what is it and why is it done that way?", "topic": "Contact Process", "tier": 1},
    {"id": 6, "text": "What types of devices are primarily used? (e.g., cell phones, landlines, radios, etc.)", "topic": "Contact Process", "tier": 1},
    
    # Section 3: Callout List Management
    {"id": 7, "text": "After the first employee, is the next person called from the same list or a different one?", "topic": "List Management", "tier": 1},
    {"id": 8, "text": "In total, how many different lists or groups are used to fully staff this callout?", "topic": "List Management", "tier": 1},
    {"id": 9, "text": "Are the lists organized by job classification (e.g., 'Linemen,' 'Supervisors')? If not, what other attribute determines the order (e.g., overtime hours, seniority, special qualifications)?", "topic": "List Management", "tier": 1},
    {"id": 10, "text": "When going through a list, do you follow a strict top-to-bottom order, or are people ever skipped?", "topic": "List Management", "tier": 1},
    {"id": 11, "text": "If employees are skipped, what are the reasons? (e.g., based on qualifications, status like vacation/sick, etc.)", "topic": "List Management", "tier": 1},
    {"id": 12, "text": "Are there any planned pauses between call attempts within the same list?", "topic": "List Management", "tier": 1},
    
    # Section 4: Handling Insufficient Staffing
    {"id": 13, "text": "If you don't get the required number of people from the primary list, what is the next step?", "topic": "Insufficient Staffing", "tier": 1},
    {"id": 14, "text": "Is the primary list called a second time before moving on to other options?", "topic": "Insufficient Staffing", "tier": 1},
    {"id": 15, "text": "In critical situations, is the position ever offered to employees who would not normally be called?", "topic": "Insufficient Staffing", "tier": 1},
    {"id": 16, "text": "Is this procedure for when staffing is insufficient always the same, or does it vary depending on the situation (e.g., major emergency vs. routine)?", "topic": "Insufficient Staffing", "tier": 1},
    
    # Section 5: Additional Rules and Logistics
    {"id": 17, "text": "Is it possible for an employee to decline the callout but ask to be contacted again if no one else accepts? How is that situation managed?", "topic": "Additional Rules", "tier": 1},
    {"id": 18, "text": "If an employee says no on the first pass through the list, are they contacted again on a second pass?", "topic": "Additional Rules", "tier": 1},
    {"id": 19, "text": "Does the order or content of the lists ever change over time? If so, how often and what triggers it (e.g., new hires, changes in qualifications, balancing of overtime)?", "topic": "Additional Rules", "tier": 2},
    {"id": 20, "text": "If the list order is based on overtime, what criteria are used as a tie-breaker if two employees have the same hours (e.g., seniority, hire date)?", "topic": "Additional Rules", "tier": 2},
    {"id": 21, "text": "Besides calls, are other methods like emails or text messages used to provide information about the callout?", "topic": "Additional Rules", "tier": 2},
    {"id": 22, "text": "Are there any rules that prevent calling someone right before or after their normal shift?", "topic": "Additional Rules", "tier": 2},
    {"id": 23, "text": "Finally, are there any rules that would excuse an employee for declining a callout without it counting against them (e.g., if it's near their vacation, a scheduled shift, etc.)?", "topic": "Additional Rules", "tier": 2},
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
        
        # Get user context
        user_name = st.session_state.user_info.get('name', 'there')
        company_name = st.session_state.user_info.get('company', 'your organization')
        utility_type = st.session_state.user_info.get('utility_type', 'utility organization')
        
        # Check if this is the last question
        is_last_question = current_question_info['id'] == len(ACE_QUESTIONS)
        
        if is_last_question:
            # Special handling for the final question
            system_prompt = f"""You are ACE, an ARCOS questionnaire assistant. This is the FINAL question.

USER: {user_name} from {company_name} ({utility_type})

🚨 FINAL QUESTION RULES:
1. You can ONLY ask this EXACT question: **{current_question_info['text']}**
2. After they answer, say "Thank you! That completes our questionnaire." and STOP
3. DO NOT ask any additional questions
4. Keep responses to 1-2 sentences maximum

FINAL QUESTION TO ASK: **{current_question_info['text']}**

RESPONSE PATTERN:
- Brief acknowledgment: "Got it!" / "Thanks!" / "Perfect."
- Ask ONLY the exact question above in bold
- STOP immediately

After their final answer, say: "Thank you! That completes our questionnaire."

EXAMPLE (only if user requests): {get_question_examples(current_question_info['id'])[0]}

You are completing a SCRIPTED questionnaire. This is the LAST question."""
        else:
            # Get the next question to ask after user answers current one
            next_question_id = current_question_info['id'] + 1
            next_question_text = ""
            if next_question_id <= len(ACE_QUESTIONS):
                next_question_text = ACE_QUESTIONS[next_question_id - 1]['text']
            
            # Simple system prompt that tells AI exactly what to do
            if next_question_text:
                system_prompt = f"""You are ACE, conducting an ARCOS questionnaire.

USER: {user_name} from {company_name} ({utility_type})

CURRENT SITUATION: User is answering question {current_question_info['id']}: "{current_question_info['text']}"

YOUR RESPONSE PATTERN:
1. Brief acknowledgment: "Got it!" / "Thanks!" / "Perfect."
2. Ask the NEXT question: **{next_question_text}**
3. STOP immediately

ONLY provide examples if user types "example" or "help": {get_question_examples(current_question_info['id'])[0]}

Ask question {next_question_id} next."""
            else:
                system_prompt = f"""You are ACE. The questionnaire is complete.

USER: {user_name} from {company_name} ({utility_type})

The user just answered the final question. Say: "Thank you! That completes our questionnaire." and STOP."""
        
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
                "max_tokens": 150,  # Keep responses very short like original ACEBot
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


class SimpleEmailService:
    """Simple email notification service"""
    
    def __init__(self):
        """Initialize email service from secrets or environment variables"""
        # Try Streamlit secrets first, then environment variables
        if hasattr(st, 'secrets'):
            self.sender_email = st.secrets.get("EMAIL_SENDER", os.getenv("EMAIL_SENDER", ""))
            self.sender_password = st.secrets.get("EMAIL_PASSWORD", os.getenv("EMAIL_PASSWORD", ""))
            self.recipient_email = st.secrets.get("EMAIL_RECIPIENT", os.getenv("EMAIL_RECIPIENT", ""))
            self.smtp_server = st.secrets.get("SMTP_SERVER", os.getenv("SMTP_SERVER", "smtp.gmail.com"))
            self.smtp_port = int(st.secrets.get("SMTP_PORT", os.getenv("SMTP_PORT", "587")))
        else:
            self.sender_email = os.getenv("EMAIL_SENDER", "")
            self.sender_password = os.getenv("EMAIL_PASSWORD", "")
            self.recipient_email = os.getenv("EMAIL_RECIPIENT", "")
            self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
            self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
    
    def is_configured(self):
        """Check if email service is properly configured"""
        return bool(self.sender_email and self.sender_password and self.recipient_email)
    
    def send_completion_notification(self, user_info, summary_text):
        """Send email notification when questionnaire is completed"""
        if not self.is_configured():
            return {"success": False, "message": "Email not configured - notification not sent"}
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            msg['Subject'] = f"ACE Questionnaire Completed - {user_info.get('name', 'Unknown')} from {user_info.get('company', 'Unknown')}"
            
            # Create email body
            body = f"""
            <html>
            <body>
            <h2>ACE Questionnaire Completed</h2>
            <p><strong>Status:</strong> ✅ Completed</p>
            <p><strong>User:</strong> {user_info.get('name', 'Unknown')}</p>
            <p><strong>Company:</strong> {user_info.get('company', 'Unknown')}</p>
            <p><strong>Email:</strong> {user_info.get('email', 'Unknown')}</p>
            <p><strong>Utility Type:</strong> {user_info.get('utility_type', 'Unknown')}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            <p><strong>Questions Answered:</strong> {len(st.session_state.answers)}/23</p>
            
            <h3>Next Steps</h3>
            <p>The completed questionnaire responses are attached as a summary file. Please review the responses to configure ARCOS according to the documented callout process.</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # Attach summary file
            attachment = MIMEApplication(summary_text.encode('utf-8'))
            company_name = user_info.get('company', 'Company').replace(' ', '_')
            filename = f"ACE_Summary_{company_name}_{datetime.now().strftime('%Y%m%d')}.md"
            attachment.add_header('Content-Disposition', 'attachment', filename=filename)
            msg.attach(attachment)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return {"success": True, "message": f"Email notification sent to {self.recipient_email}"}
        
        except Exception as e:
            return {"success": False, "message": f"Failed to send email: {str(e)}"}


def init_session_state():
    """Initialize simple, reliable session state"""
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 1
    
    if 'answers' not in st.session_state:
        st.session_state.answers = {}
    
    if 'conversation' not in st.session_state:
        st.session_state.conversation = []
    
    if 'user_info' not in st.session_state:
        st.session_state.user_info = {"name": "", "company": "", "email": "", "utility_type": ""}
    
    if 'completed' not in st.session_state:
        st.session_state.completed = False
    
    if 'started' not in st.session_state:
        st.session_state.started = False
    
    if 'summary_text' not in st.session_state:
        st.session_state.summary_text = ""

def get_current_question():
    """Get current question info"""
    current_num = st.session_state.current_question
    if current_num <= len(ACE_QUESTIONS):
        return ACE_QUESTIONS[current_num - 1]
    return None

def get_question_examples(question_id):
    """Get specific examples for each question showing ideal customer responses"""
    examples = {
        1: [  # Describe the type of situation or event that triggers this callout process
            "We use this callout process for power outages affecting 500 or more customers, typically caused by storms, equipment failures, or vehicle accidents that damage our infrastructure.",
            "This process is triggered when we receive reports of gas leaks from the public or our automated detection systems. Safety is our top priority, so we respond immediately.",
            "We activate callouts for water main breaks that disrupt service to neighborhoods. These usually happen due to aging infrastructure, ground shifts, or extreme weather conditions."
        ],
        2: [  # How many employees, and with which roles or job classifications, are typically required?
            "For power restoration, we typically need 2 journeyman linemen and 1 crew supervisor. The supervisor coordinates with dispatch while the linemen handle the actual repair work.",
            "Gas leak responses require 1 certified gas technician and 1 safety officer. The technician handles the repair while the safety officer manages the scene and coordinates with emergency services if needed.",
            "Water main breaks usually need 3 field technicians and 1 crew leader. Two technicians work on the repair, one operates equipment, and the leader coordinates with customers and traffic control."
        ],
        3: [  # Who is contacted first, and what is the main reason?
            "We contact our on-call supervisor first because they need to assess the situation, coordinate resources, and determine if additional specialized crews or equipment are needed before dispatching field workers.",
            "Our lead technician gets the first call because they have 15 years of experience and can quickly determine the scope of work needed. They also coordinate with other crew members and ensure we have the right tools on site.",
            "We call our operations dispatcher first since they maintain real-time visibility of all crew locations and availability. They can immediately identify the closest available team and coordinate multiple crews if needed."
        ],
        4: [  # How many devices are used to try and reach them?
            "We try to reach them on two devices: their company cell phone first, then their personal cell phone if there's no answer within 2 minutes.",
            "Three devices: we start with their office phone, then try their mobile phone, and finally use the two-way radio system if they're already in the field.",
            "Just one primary device - their assigned work cell phone. Everyone is required to keep it on and charged during their on-call periods."
        ],
        5: [  # Are those devices contacted one by one or all at the same time?
            "We contact them sequentially - work phone first, wait 2 minutes for a response, then try their personal cell. This gives them time to answer before we move to the next device.",
            "We call both their work phone and personal cell simultaneously because emergency situations require the fastest possible response time.",
            "One by one in order: office phone first, then mobile after 30 seconds if no answer. We don't want to overwhelm them with multiple calls at once."
        ],
        6: [  # What types of devices are primarily used?
            "Primarily cell phones because our crews need to be mobile and reachable whether they're at home, in the field, or traveling between job sites.",
            "We use a combination of two-way radios for field communication and cell phones for initial contact. Radios work better in remote areas where cell coverage is spotty.",
            "Company-issued smartphones with our emergency response app installed. The app shows incident details, maps, and allows crews to update their status in real-time."
        ],
        7: [  # After the first employee, is the next person called from the same list?
            "Same list - we continue down our supervisor list in order based on overtime hours until we get the required number of people.",
            "Different list - once we have a supervisor, we move to our technician list to get the field workers needed for the job.",
            "We stay on the same list until it's exhausted, then move to our backup list from the neighboring district."
        ],
        8: [  # How many different lists or groups are used?
            "We use three main lists: supervisors, journeyman technicians, and apprentices. Each has different qualifications and we need specific combinations depending on the job type.",
            "Two lists total: our primary crew list with full-time employees, and our backup contractor list that we use when the primary crew is unavailable or we need additional resources.",
            "Four different lists: operations supervisors, field technicians, equipment operators, and our approved contractor vendors. Complex jobs might require people from multiple lists."
        ],
        9: [  # Are the lists organized by job classification or other attribute?
            "Lists are organized by job classification first - supervisors, journeymen, apprentices - then within each classification they're ordered by overtime hours worked, with lowest hours called first.",
            "We organize primarily by overtime balance. Everyone's hours are tracked and updated weekly, so the person with the fewest overtime hours gets called first regardless of their specific job title.",
            "Geographic location is our main organizing principle. We have separate lists for each service territory, and we call the closest available crew to minimize response time."
        ],
        10: [  # Do you follow strict top-to-bottom order or skip around?
            "Strict top-to-bottom order based on overtime hours. This ensures fair distribution of overtime opportunities and everyone knows exactly where they stand on the list.",
            "We skip people who are on vacation, sick leave, or have other approved time off. Our dispatcher maintains a daily availability list to know who to skip.",
            "Generally top-to-bottom, but we'll skip someone if they don't have the required certifications for that specific type of work. For example, not everyone is qualified for high-voltage repairs."
        ],
        11: [  # If employees are skipped, what are the reasons?
            "We skip employees who are on approved vacation time, sick leave, or have submitted time-off requests that were already approved by their supervisor.",
            "Main reasons for skipping: they lack the required certification for the specific work, they're currently assigned to another emergency call, or they're outside our response area.",
            "We skip people who are too far from the incident location - if someone is more than 45 minutes away and we have closer options, we'll call the closer crew first."
        ],
        12: [  # Are there any planned pauses between call attempts?
            "Yes, we wait 2 minutes between each person to give them adequate time to answer. People might be in the shower, driving, or need a moment to check their availability.",
            "No planned pauses - we call continuously down the list until someone answers. In emergency situations, speed is more important than convenience.",
            "We pause for 5 minutes after every 3rd call to reassess the situation and make sure we're still calling the right type of personnel for what's actually needed."
        ],
        13: [  # If you don't get required number from primary list, what's next?
            "We contact our mutual aid partners in the neighboring utility district. We have formal agreements to help each other during emergencies and they usually have crews available.",
            "Our next step is calling approved contractors from our vendor list. These are pre-qualified companies that meet our safety standards and know our systems.",
            "We escalate to our emergency management coordinator who can authorize calling in off-duty employees on overtime or request assistance from other departments."
        ],
        14: [  # Is primary list called second time before other options?
            "Yes, we go through our primary list twice before moving to contractors. Sometimes people's situations change or they didn't hear the first call.",
            "No, we immediately move to our backup district crew. If our primary people aren't available, we need to get resources mobilized quickly rather than waste time on repeat calls.",
            "Only during critical emergencies like major storms. For routine callouts, we use contractors if the first pass through our list doesn't get enough people."
        ],
        15: [  # In critical situations, offer to employees not normally called?
            "During major storms, we'll contact recently retired employees who still maintain their certifications and are willing to help during emergencies. They know our systems and can be very valuable.",
            "Yes, we'll ask office staff to help with non-technical support roles like coordinating with customers, managing logistics, or handling paperwork so field crews can focus on repairs.",
            "We'll call in off-duty employees from other shifts and offer overtime pay. During major outages, we need all hands on deck and most people are willing to help."
        ],
        16: [  # Is insufficient staffing procedure always the same or varies?
            "Same procedure every time - consistency is important so everyone knows what to expect. We always follow the same escalation process regardless of the situation type.",
            "It varies by emergency type. Storm responses get different treatment than routine repairs - we'll mobilize contractors faster and call in more resources for weather-related emergencies.",
            "Different procedures for weekends versus weekdays because contractor availability changes and our mutual aid agreements have different response times on weekends."
        ],
        17: [  # Can employee decline but ask to be contacted again?
            "Yes, they can say 'call me back if no one else accepts the callout.' This usually happens when they have a family commitment but could rearrange things if we really need them.",
            "No, once someone declines a callout, they're marked unavailable for that specific incident. We don't want to put pressure on people or create confusion about who's actually coming in.",
            "Only for non-emergency situations. During routine maintenance callouts, people can ask to be called back, but for emergency responses we need definitive yes or no answers."
        ],
        18: [  # If someone says no on first pass, contacted on second pass?
            "No, if they declined on the first pass, we respect that decision and don't call them again for that same incident. It would be unfair to pressure people who already said no.",
            "Yes, we do call them again on the second pass because their circumstances might have changed, or they might reconsider if they know we're really short-staffed.",
            "We only call them again if absolutely no one else accepted and it's a critical emergency. In that case, we explain the situation has escalated and ask if they can help."
        ],
        19: [  # Does order/content of lists change over time?
            "We update the lists monthly based on overtime hours worked. As people accumulate overtime, they move down the list so the burden gets distributed fairly among all employees.",
            "Lists are updated immediately whenever we have new hires, retirements, or people change positions. Our HR department notifies operations within 24 hours of any personnel changes.",
            "Quarterly rebalancing to make sure callout frequency is distributed evenly. We track how often each person gets called and adjust the order to ensure fairness."
        ],
        20: [  # What criteria for tie-breaker if same overtime hours?
            "Seniority is our first tie-breaker - the person who's been with the company longer gets called first when overtime hours are equal.",
            "We use hire date as the tie-breaker, but in reverse - the most recently hired person gets called first. This helps newer employees get overtime opportunities to supplement their income.",
            "Alphabetical order by last name. It's simple, fair, and removes any appearance of favoritism when people have identical overtime hours."
        ],
        21: [  # Other methods like emails or text messages?
            "We send text messages after making successful phone contact to provide incident details, location information, and estimated duration. The text serves as a written record of the assignment.",
            "Email notifications go to supervisors and management to keep them informed about callout status and crew assignments, but we don't use email for the actual callouts since it's not immediate enough.",
            "No, we only use phone calls for the actual callouts. Text and email aren't reliable enough for emergency situations where immediate response is critical."
        ],
        22: [  # Rules preventing calls before/after normal shift?
            "We avoid calling anyone within 2 hours of their scheduled shift start or end time. This gives people time to rest between shifts and ensures they're alert when they come to work.",
            "No restrictions - emergencies don't follow normal business hours. If we need someone, we call them regardless of when their shift starts or ends.",
            "We try to avoid calls 1 hour before scheduled shifts when possible, but during major emergencies those rules get suspended and we call whoever we need."
        ],
        23: [  # Rules that excuse declined callouts?
            "Vacation requests that were approved in advance automatically excuse someone from declining a callout. We also excuse people for medical appointments or documented family emergencies.",
            "If someone worked within the past 8 hours, they can decline without it counting against them. We want people to be rested and safe.",
            "No formal excuses - being available for callouts is part of the job expectations. However, supervisors use discretion for legitimate personal emergencies."
        ]
    }
    
    return examples.get(question_id, ["Provide specific details about your current process"])

def infer_utility_type(company_name):
    """Infer utility type from company name"""
    company_lower = company_name.lower()
    
    # Electric utilities
    electric_keywords = ['electric', 'power', 'energy', 'grid', 'transmission', 'distribution']
    if any(keyword in company_lower for keyword in electric_keywords):
        return "electric utility"
    
    # Gas utilities
    gas_keywords = ['gas', 'natural gas', 'lng', 'pipeline']
    if any(keyword in company_lower for keyword in gas_keywords):
        return "gas utility"
    
    # Water utilities
    water_keywords = ['water', 'wastewater', 'sewer', 'municipal']
    if any(keyword in company_lower for keyword in water_keywords):
        return "water utility"
    
    # Telecommunications
    telecom_keywords = ['telecom', 'telephone', 'communications', 'broadband', 'fiber']
    if any(keyword in company_lower for keyword in telecom_keywords):
        return "telecommunications utility"
    
    # Multi-utility or generic
    utility_keywords = ['utility', 'utilities', 'public service']
    if any(keyword in company_lower for keyword in utility_keywords):
        return "utility company"
    
    # Default if no clear match
    return "utility organization"

def display_progress():
    """Beautiful, encouraging progress display"""
    current = st.session_state.current_question
    total = len(ACE_QUESTIONS)
    progress = min((current - 1) / total, 1.0)  # -1 because we show progress after completing questions
    
    # Progress bar styling is now in main CSS
    
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
    
    # Check for very short answers (might need more detail)
    words = user_input.strip().split()
    if len(words) <= 2 and len(user_input.strip()) < 10:
        return True
        
    # Check for vague responses
    if any(vague in user_lower for vague in vague_responses):
        return True
    
    return False

def update_realtime_summary(question_id, answer_text):
    """Update the summary in real-time as each question is answered"""
    question = next((q for q in ACE_QUESTIONS if q["id"] == question_id), None)
    if not question:
        return
    
    # Initialize summary if starting fresh
    if not st.session_state.summary_text:
        st.session_state.summary_text = f"""# ACE Questionnaire Summary
**Participant:** {st.session_state.user_info.get('name', 'Unknown')}
**Company:** {st.session_state.user_info.get('company', 'Unknown')}
**Email:** {st.session_state.user_info.get('email', 'Unknown')}
**Utility Type:** {st.session_state.user_info.get('utility_type', 'Unknown')}
**Date:** {datetime.now().strftime('%B %d, %Y')}
**Questions Completed:** 0/{len(ACE_QUESTIONS)}

"""
        # Initialize topic sections
        topics_initialized = set()
    
    # Add this Q&A to the appropriate topic section
    topic = question["topic"]
    qa_entry = f"""**Q:** {question['text']}
**A:** {answer_text}

"""
    
    # Check if this topic section exists in the summary
    if f"## {topic}" not in st.session_state.summary_text:
        # Add new topic section
        st.session_state.summary_text += f"## {topic}\n{qa_entry}"
    else:
        # Append to existing topic section
        # Find the position to insert (before next topic or at end)
        topic_start = st.session_state.summary_text.find(f"## {topic}")
        next_topic_start = st.session_state.summary_text.find("## ", topic_start + 1)
        
        if next_topic_start == -1:
            # This is the last topic, append at end
            st.session_state.summary_text += qa_entry
        else:
            # Insert before next topic
            st.session_state.summary_text = (
                st.session_state.summary_text[:next_topic_start] + 
                qa_entry + 
                st.session_state.summary_text[next_topic_start:]
            )
    
    # Update the questions completed count
    completed_count = len(st.session_state.answers)
    st.session_state.summary_text = st.session_state.summary_text.replace(
        f"**Questions Completed:** {completed_count-1}/{len(ACE_QUESTIONS)}",
        f"**Questions Completed:** {completed_count}/{len(ACE_QUESTIONS)}"
    )

def find_next_relevant_question(start_question_num, answers):
    """Smart question skipping based on previous answers (like original ACEBot)"""
    current_num = start_question_num
    
    # Skip questions based on previous answers to avoid redundancy
    while current_num <= len(ACE_QUESTIONS):
        current_q = ACE_QUESTIONS[current_num - 1]  # Convert to 0-indexed
        
        # Check if this question should be skipped based on previous answers
        should_skip = False
        
        # Get all previous answers as text
        all_previous_answers = " ".join(answers.values()).lower()
        
        # Question-specific skip logic (like original ACEBot)
        if current_q["id"] == 6:  # "How many people do you typically call out?"
            # Skip if already mentioned numbers in staffing questions
            if any(word in all_previous_answers for word in ["2", "3", "4", "5", "crew", "team", "people", "employees"]):
                should_skip = True
                
        elif current_q["id"] == 8:  # "Are your lists organized by job classification?"
            # Skip if already mentioned job classes or roles
            if any(word in all_previous_answers for word in ["supervisor", "foreman", "technician", "journeyman", "apprentice", "classification", "role", "job"]):
                should_skip = True
                
        elif current_q["id"] == 11:  # "Do you use overtime ordering?"
            # Skip if they clearly don't use overtime systems
            if any(phrase in all_previous_answers for phrase in ["no overtime", "don't use overtime", "rotation", "rotating", "weekly", "standby"]):
                should_skip = True
                
        elif current_q["id"] == 14:  # "Are there delays between calling different groups?"
            # Skip if they mentioned single list or no multiple groups
            if any(phrase in all_previous_answers for phrase in ["one list", "single list", "same list", "don't have multiple"]):
                should_skip = True
                
        elif current_q["id"] == 17:  # "How do you handle list changes over time?"
            # Skip if they already explained list management in detail
            if any(word in all_previous_answers for word in ["update", "change", "quarterly", "monthly", "weekly", "automatic"]) and len(all_previous_answers) > 200:
                should_skip = True
                
        # If we should skip, try next question
        if should_skip:
            current_num += 1
        else:
            break
    
    return current_num

def generate_summary():
    """Generate a clean summary of all answers"""
    if not st.session_state.answers:
        return "No responses recorded."
    
    summary = f"# ACE Questionnaire Summary\n"
    summary += f"**Participant:** {st.session_state.user_info.get('name', 'Unknown')}\n"
    summary += f"**Company:** {st.session_state.user_info.get('company', 'Unknown')}\n"
    summary += f"**Email:** {st.session_state.user_info.get('email', 'Unknown')}\n"
    summary += f"**Utility Type:** {st.session_state.user_info.get('utility_type', 'Unknown')}\n"
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
    
    # Custom CSS for ARCOS brand styling (red/white theme)
    st.markdown("""
        <style>
        .main-header {
            text-align: center;
            padding: 1.2rem 0;
            background: #E31E24;
            color: white;
            border-radius: 8px;
            margin-bottom: 1.5rem;
        }
        .main-header h1 {
            font-size: 2.2rem !important;
            margin-bottom: 0.3rem !important;
        }
        .main-header p {
            font-size: 1rem !important;
            margin: 0 !important;
            opacity: 0.9;
        }
        .stButton > button {
            background: #E31E24;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 0.5rem 1.5rem;
            font-weight: bold;
        }
        .stButton > button:hover {
            background: #c41e20;
            border: none;
        }
        .stProgress > div > div > div > div {
            background: linear-gradient(90deg, #E31E24, #ff4444) !important;
        }
        /* Sidebar styling */
        .css-1d391kg {
            padding-top: 1rem;
        }
        /* Compact sidebar text */
        .sidebar .element-container {
            margin-bottom: 0.5rem;
        }
        /* Make example text smaller and more compact */
        .sidebar .stMarkdown {
            font-size: 0.85rem;
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
    email_service = SimpleEmailService()
    
    # Compact Sidebar
    with st.sidebar:
        # Compact progress section
        st.markdown("### 📊 Progress")
        display_progress()
        
        # Compact user info
        if st.session_state.user_info["name"]:
            st.markdown(f"👋 **{st.session_state.user_info['name']}**")
            if st.session_state.user_info["company"]:
                st.markdown(f"🏢 {st.session_state.user_info['company']}")
        
        # Current focus - more compact
        current_q = get_current_question()
        if current_q:
            st.markdown("---")
            st.markdown("### 🎯 Current")
            st.markdown(f"**{current_q['topic']}** (Tier {current_q['tier']})")
        
        # Always show guidance section when questionnaire is active
        if st.session_state.started and current_q:
            # Compact example section
            st.markdown("### 💡 Example")
            examples = get_question_examples(current_q['id'])
            if examples:
                # Show only the first example in a more compact format
                current_example = examples[0]
                # Truncate if too long but show more than before
                if len(current_example) > 200:
                    display_example = current_example[:200] + "..."
                else:
                    display_example = current_example
                st.markdown(f"*\"{display_example}\"*")
            
            # Compact help text
            st.markdown("💬 *Type 'example' for help*")
        
        st.markdown("---")
        # Compact reset button
        if st.button("🔄 Reset", help="Start questionnaire over"):
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
            # Download summary - use real-time summary instead of generating
            st.download_button(
                label="📥 Download Summary",
                data=st.session_state.summary_text,
                file_name=f"ACE_Summary_{st.session_state.user_info.get('company', 'Company')}_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown"
            )
            
            # Email notification
            if email_service.is_configured():
                if st.button("📧 Send Email Notification", type="secondary"):
                    with st.spinner("Sending email..."):
                        result = email_service.send_completion_notification(st.session_state.user_info, st.session_state.summary_text)
                        if result["success"]:
                            st.success(f"✅ {result['message']}")
                        else:
                            st.error(f"❌ {result['message']}")
            else:
                st.info("📧 Email notifications not configured")
        
        # Show detailed responses
        if st.expander("📖 View All Responses", expanded=False):
            st.markdown(st.session_state.summary_text)
            
    else:
        # Main conversation flow
        if not st.session_state.started:
            # Welcome screen
            st.markdown("""
                ### 👋 Welcome to the ACE Questionnaire!
                
                I'm here to help you document your organization's callout processes for ARCOS implementation. 
                This streamlined questionnaire should take about **10-15 minutes** and will help ensure ARCOS is configured perfectly for your needs.
                
                **What to expect:**
                - 23 focused questions covering 5 key areas of your callout process
                - I'll ask you questions about how you currently handle callouts
                - Feel free to ask for examples if anything is unclear  
                - We'll go through this step-by-step at your pace
                
                ---
                
                **📋 Data Privacy Notice**
                
                **IMPORTANT: Data Privacy Notice**
                
                Please DO NOT enter any Personal Identifying Information (PII) such as social security numbers, home addresses, personal phone numbers, or other sensitive personal data. Focus on business processes, job roles, and organizational procedures only.
                
                ---
                
                **📝 Please provide your information to get started:**
            """)
            
            # User information form
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("👤 Your Name", placeholder="e.g., John Smith")
                company = st.text_input("🏢 Company/Organization", placeholder="e.g., ABC Electric Utility")
            with col2:
                email = st.text_input("📧 Email Address", placeholder="e.g., john.smith@abcelectric.com")
                st.write("")  # Spacer for alignment
            
            st.markdown("---")
            
            # Validation and start button
            if name and company and email:
                if st.button("🚀 Let's Begin!", type="primary"):
                    # Store user information
                    st.session_state.user_info["name"] = name.strip()
                    st.session_state.user_info["company"] = company.strip()
                    st.session_state.user_info["email"] = email.strip()
                    st.session_state.user_info["utility_type"] = infer_utility_type(company)
                    
                    st.session_state.started = True
                    
                    # Add welcome message to conversation with utility type context
                    utility_type = st.session_state.user_info["utility_type"]
                    welcome_msg = f"""Hi {name}! I'm ACE, your questionnaire assistant. I see you work for a {utility_type}. Let's start documenting your callout process with our streamlined 23-question format.

**{ACE_QUESTIONS[0]['text']}**"""
                
                    st.session_state.conversation.append({"role": "assistant", "content": welcome_msg})
                    st.rerun()
            else:
                st.info("Please fill in all fields to continue.")
        
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
                            # Add AI response to conversation first
                            st.session_state.conversation.append({"role": "assistant", "content": ai_response})
                            
                            # AGGRESSIVE ADVANCEMENT: Check if user provided substantive answer
                            # Don't advance only for these specific cases:
                            # 1. Very short responses that don't address the question
                            # 2. Obvious requests for help/examples
                            # 3. AI explicitly asking for clarification with question words
                            
                            user_input_lower = user_input.lower().strip()
                            ai_response_lower = ai_response.lower()
                            
                            # Check if user gave a very short non-substantive response
                            is_too_short = len(user_input.strip()) < 5
                            
                            # Check if AI is asking clarifying questions about the SAME topic (not next question)
                            # Only consider it clarification if AI is asking for more details WITHOUT bold question
                            has_bold_question = "**" in ai_response
                            has_question_mark = "?" in ai_response
                            has_clarification_words = any(word in ai_response_lower for word in ["could you elaborate", "can you provide more", "could you be more specific", "what do you mean", "can you clarify"])
                            
                            is_ai_asking_clarification = (
                                has_question_mark and 
                                has_clarification_words and
                                not has_bold_question  # If there's a bold question, it's likely the next question
                            )
                            
                            # Check if user is asking for help
                            is_user_help_request = any(phrase in user_input_lower for phrase in ["example", "help", "?", "what do you mean", "clarify", "explain"])
                            
                            # ADVANCE UNLESS we shouldn't
                            should_not_advance = (
                                is_too_short or 
                                is_ai_asking_clarification or 
                                is_user_help_request
                            )
                            
                            if not should_not_advance:
                                # Store answer 
                                st.session_state.answers[current_q["id"]] = user_input
                                
                                # Update real-time summary immediately
                                update_realtime_summary(current_q["id"], user_input)
                                
                                # Check if this was the last question (question 23)
                                if st.session_state.current_question == len(ACE_QUESTIONS):
                                    # We just answered the final question - questionnaire is complete!
                                    st.session_state.completed = True
                                else:
                                    # Smart question skipping based on previous answers
                                    original_next_question = st.session_state.current_question + 1
                                    next_question = find_next_relevant_question(original_next_question, st.session_state.answers)
                                    
                                    if next_question > len(ACE_QUESTIONS):
                                        # Skipped to beyond the last question
                                        st.session_state.completed = True
                                    else:
                                        st.session_state.current_question = next_question
                            # If it's clarification or no next question found, don't advance (stay on current question)
                    
                    st.rerun()

if __name__ == "__main__":
    main()