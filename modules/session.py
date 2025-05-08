# modules/session.py
import json
import time
import streamlit as st
from datetime import datetime
import os

# Import only after conditional import check
try:
    from config import TOPIC_AREAS
except ImportError:
    # Default config values if config module is not available
    TOPIC_AREAS = {
        "basic_info": "Basic Information",
        "staffing_details": "Staffing Details",
        "contact_process": "Contact Process",
        "list_management": "List Management",
        "insufficient_staffing": "Insufficient Staffing",
        "calling_logistics": "Calling Logistics",
        "list_changes": "List Changes", 
        "tiebreakers": "Tiebreakers",
        "additional_rules": "Additional Rules"
    }
    
try:
    from modules.server_storage import ServerStorage
except ImportError:
    # Define a minimal version if not available
    class ServerStorage:
        def __init__(self, *args, **kwargs):
            pass
        def save_session(self, session_data):
            return {"success": False, "message": "Server storage not available"}
        def load_session(self, session_id):
            return {"success": False, "message": "Server storage not available"}

class SessionManager:
    def __init__(self):
        """Initialize the session manager with server-based storage as the primary method."""
        # Initialize server storage
        self.server_storage = ServerStorage()
        
    def get_session_state(self):
        """Return the current session state data structure."""
        if 'user_info' not in st.session_state:
            self._initialize_session_state()
            
        return {
            "user_info": st.session_state.user_info,
            "responses": st.session_state.responses,
            "current_question_index": st.session_state.current_question_index,
            "chat_history": st.session_state.chat_history,
            "visible_messages": st.session_state.visible_messages,
            "topic_areas_covered": st.session_state.topic_areas_covered,
            "saved_timestamp": datetime.now().isoformat(),
            "version": "3.1"  # Updated version for enhanced context restoration
        }
    
    def _initialize_session_state(self):
        """Initialize the session state with default values."""
        st.session_state.user_info = {"name": "", "company": ""}
        st.session_state.responses = []
        st.session_state.current_question_index = 0
        
        if 'questions' not in st.session_state:
            from utils.helpers import load_questions
            st.session_state.questions = load_questions('data/questions.txt')
            
        st.session_state.current_question = st.session_state.questions[0]
        
        if 'instructions' not in st.session_state:
            from utils.helpers import load_instructions
            st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
            
        st.session_state.chat_history = [{"role": "system", "content": st.session_state.instructions}]
        st.session_state.visible_messages = []
        
        # Initialize topic tracking
        st.session_state.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
        st.session_state.summary_requested = False
        st.session_state.explicitly_finished = False
        st.session_state.restoring_session = False
        st.session_state.api_request_in_progress = False  # Added for progress indicator
        st.session_state.theme = "light"  # Default theme setting
        
        # Add initial greeting that includes the first question
        welcome_message = "👋 Hello! This questionnaire is designed to help ARCOS solution consultants better understand your company's requirements. If you're unsure about any question, simply type a ? and I'll provide a brief explanation. You can also type 'example' or click the 'Example' button to see a sample response.\n\nLet's get started! Could you please provide your name and your company name?"
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
        st.session_state.visible_messages.append({"role": "assistant", "content": welcome_message})

    def save_session(self):
        """Save the current session state to server storage or file."""
        try:
            # Get session data
            session_data = self.get_session_state()
            
            # Clean up the chat history for serialization
            clean_chat_history = []
            for msg in session_data["chat_history"]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    clean_chat_history.append({"role": msg["role"], "content": msg["content"]})
            session_data["chat_history"] = clean_chat_history
            
            # Clean up visible messages
            clean_visible_messages = []
            for msg in session_data["visible_messages"]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    # Remove any temporary flags used for display logic
                    cleaned_msg = {"role": msg["role"], "content": msg["content"]}
                    clean_visible_messages.append(cleaned_msg)
            session_data["visible_messages"] = clean_visible_messages
            
            # Try to save to server storage (primary method)
            server_result = self.server_storage.save_session(session_data)
            server_success = server_result.get("success", False)
            session_id = server_result.get("session_id", "")
            
            # Return the result
            if server_success:
                return {
                    "success": True,
                    "method": "server",
                    "message": "Session saved to server.",
                    "session_id": session_id
                }
            else:
                # Return serialized data for file download as fallback
                return {
                    "success": True, 
                    "method": "file", 
                    "message": "Server storage unavailable. Please download the file.",
                    "data": json.dumps(session_data)
                }
                
        except Exception as e:
            return {"success": False, "message": f"Error saving session: {str(e)}"}
    
    def _find_topic_answers(self, session_data, topic):
        """Find 1-2 sample answers for a given topic area to include in context."""
        # Map topics to related keywords
        topic_keywords = {
            "basic_info": ["name", "company", "callout type", "situation"],
            "staffing_details": ["employee", "staff", "role", "classification"],
            "contact_process": ["contact first", "device", "call first", "phone"],
            "list_management": ["list", "skip", "traverse", "straight down"],
            "insufficient_staffing": ["required number", "don't get", "not enough"],
            "calling_logistics": ["simultaneous", "call again", "second pass"],
            "list_changes": ["change", "update", "overtime hours"],
            "tiebreakers": ["tie", "tiebreaker", "seniority"],
            "additional_rules": ["text alert", "email", "rule", "shift"]
        }
        
        # Get related responses
        sample_answers = []
        
        if "responses" in session_data:
            for question, answer in session_data["responses"]:
                # Check if this question relates to our topic
                q_lower = question.lower()
                if any(keyword in q_lower for keyword in topic_keywords.get(topic, [])):
                    # Truncate long answers
                    short_answer = answer[:50] + "..." if len(answer) > 50 else answer
                    sample_answers.append(f"{short_answer}")
                    if len(sample_answers) >= 2:  # Limit to 2 examples
                        break
        
        return sample_answers if sample_answers else ["information provided"]
    
    def restore_session(self, source="file", file_data=None, session_id=None):
        """
        Restore a saved session from server or file with enhanced context.
        
        Args:
            source: "server" or "file"
            file_data: JSON string data if source is "file"
            session_id: Session ID if source is "server"
            
        Returns:
            dict: Result of the operation
        """
        try:
            # Set a flag to prevent infinite reruns
            if st.session_state.get("restoring_session", False):
                return {"success": False, "message": "Already restoring a session."}
            
            # Mark that we're restoring a session
            st.session_state.restoring_session = True
            
            # Get session data from source
            session_data = None
            if source == "server" and session_id:
                server_result = self.server_storage.load_session(session_id)
                if server_result.get("success", False):
                    session_data = server_result.get("session_data")
            elif source == "file" and file_data:
                session_data = json.loads(file_data)
            
            if not session_data:
                st.session_state.restoring_session = False
                return {"success": False, "message": f"No saved session found in {source}."}
            
            # Check session format version
            if "version" not in session_data:
                # Handle legacy format
                print("Legacy session format detected, attempting conversion")
            
            # Restore session state
            if "user_info" in session_data:
                st.session_state.user_info = session_data["user_info"]
            
            if "responses" in session_data:
                st.session_state.responses = session_data["responses"]
            
            if "current_question_index" in session_data:
                st.session_state.current_question_index = session_data["current_question_index"]
                # Make sure questions are loaded
                if "questions" not in st.session_state:
                    from utils.helpers import load_questions
                    st.session_state.questions = load_questions('data/questions.txt')
                
                # Set current question based on index
                if st.session_state.current_question_index < len(st.session_state.questions):
                    st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]
                else:
                    # Handle edge case where index is out of bounds
                    st.session_state.current_question_index = 0
                    st.session_state.current_question = st.session_state.questions[0]
            
            # Restore chat history - this is critical for AI context
            if "chat_history" in session_data and len(session_data["chat_history"]) > 0:
                # Make sure instructions are loaded
                if "instructions" not in st.session_state:
                    from utils.helpers import load_instructions
                    st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
                
                # Check if system prompt is first message, if not add it
                if session_data["chat_history"][0].get("role") != "system":
                    session_data["chat_history"].insert(0, {"role": "system", "content": st.session_state.instructions})
                    
                # Get information about covered topics for enhanced context
                covered_topics = []
                missing_topics = []
                recent_questions = []
                
                # Gather information about topics
                for topic, is_covered in session_data.get('topic_areas_covered', {}).items():
                    if is_covered:
                        # Find sample answers for this topic
                        topic_answers = self._find_topic_answers(session_data, topic)
                        if topic_answers:
                            covered_topics.append(f"{TOPIC_AREAS[topic]}: {', '.join(topic_answers)}")
                        else:
                            covered_topics.append(f"{TOPIC_AREAS[topic]}")
                    else:
                        missing_topics.append(TOPIC_AREAS[topic])
                
                # Get the most recent questions and answers
                if len(session_data.get("visible_messages", [])) >= 4:
                    messages = session_data["visible_messages"][-4:]
                    for msg in messages:
                        if msg["role"] == "assistant" and "?" in msg["content"]:
                            recent_questions.append(msg["content"])
                        
                # Get current and upcoming questions based on index
                current_q_index = session_data.get('current_question_index', 0)
                current_q = st.session_state.questions[min(current_q_index, len(st.session_state.questions)-1)]
                
                # Create a much more detailed context restoration message
                restoration_context = {
                    "role": "system",
                    "content": f"""
                    CRITICAL CONTEXT RESTORATION:
                    
                    1. This conversation is being resumed from a previous session.
                    2. User name: {session_data['user_info'].get('name', 'unknown')}
                    3. Company: {session_data['user_info'].get('company', 'unknown company')}
                    4. Current question index: {current_q_index}
                    5. Current question: {current_q}
                    6. Last active timestamp: {session_data.get('saved_timestamp', 'unknown')}
                    
                    Topics already covered in detail:
                    {'; '.join(covered_topics)}
                    
                    Topics still needed:
                    {', '.join(missing_topics)}
                    
                    Recent conversation context:
                    {'; '.join(recent_questions) if recent_questions else 'No recent questions found'}
                    
                    YOU MUST:
                    - Continue the conversation naturally from where it left off
                    - DO NOT repeat questions that have already been asked
                    - FOCUS on gathering information about missing topics: {', '.join(missing_topics)}
                    - Acknowledge that the conversation is being resumed
                    - Maintain a friendly, conversational tone
                    - If the user seems confused, briefly remind them where you were in the conversation
                    - If you want to summarize what you've learned so far to help reestablish context, do so BRIEFLY (1-2 sentences max)
                    - Respect any previous statements about skipping certain questions or topics
                    
                    When a topic is marked as covered, it means the user has provided substantial information about it. However, you may still need to ask follow-up questions to get more specific details.
                    """
                }
                
                # Add restoration context
                session_data["chat_history"].append(restoration_context)
                
                # Set the chat history
                st.session_state.chat_history = session_data["chat_history"]
            else:
                # If no chat history, initialize with system prompt
                if "instructions" not in st.session_state:
                    from utils.helpers import load_instructions
                    st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
                
                st.session_state.chat_history = [{"role": "system", "content": st.session_state.instructions}]
            
            # Restore visible messages for UI
            if "visible_messages" in session_data:
                st.session_state.visible_messages = session_data["visible_messages"]
            
            # Restore topic tracking
            if "topic_areas_covered" in session_data:
                # Initialize with defaults first
                st.session_state.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
                # Then update with saved values
                for topic, covered in session_data["topic_areas_covered"].items():
                    if topic in st.session_state.topic_areas_covered:
                        st.session_state.topic_areas_covered[topic] = covered
            
            # Restore summary state if applicable
            if "summary_requested" in session_data:
                st.session_state.summary_requested = session_data["summary_requested"]
            
            if "explicitly_finished" in session_data:
                st.session_state.explicitly_finished = session_data["explicitly_finished"]
            
            # Restore theme setting if available
            if "theme" in session_data:
                st.session_state.theme = session_data["theme"]
            
            # Add a visible message informing the user that the session was restored
            st.session_state.visible_messages.append({
                "role": "assistant", 
                "content": f"👋 Welcome back! I've restored your previous session. We were discussing {current_q}. Let's continue from where we left off."
            })
            
            # Mark restoration as complete
            st.session_state.restoring_session = False
            
            return {"success": True, "message": f"Session restored from {source} successfully."}
            
        except Exception as e:
            st.session_state.restoring_session = False
            return {"success": False, "message": f"Error restoring session: {str(e)}"}