# modules/session.py
import json
import time
import streamlit as st
from datetime import datetime
from streamlit_cookies_manager import EncryptedCookieManager
import os
from config import COOKIE_PREFIX, COOKIE_PASSWORD_ENV, COOKIE_DEFAULT_PASSWORD, COOKIE_KEYS, TOPIC_AREAS

class SessionManager:
    def __init__(self):
        """Initialize the session manager with both cookie and file-based storage options."""
        self.cookies = self._init_cookie_manager()
        
    def _init_cookie_manager(self):
        """Initialize the cookie manager with appropriate encryption."""
        cookie_password = os.environ.get(COOKIE_PASSWORD_ENV, COOKIE_DEFAULT_PASSWORD)
        
        cookies = EncryptedCookieManager(
            prefix=COOKIE_PREFIX,
            password=cookie_password,
        )
        
        if not cookies.ready():
            st.error("Cookie manager initialization failed. File storage will be used as fallback.")
            return None
        
        return cookies
    
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
            "version": "2.0"  # Session format version for compatibility checks
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
        
        # Add initial greeting that includes the first question
        welcome_message = "👋 Hello! This questionnaire is designed to help ARCOS solution consultants better understand your company's requirements. If you're unsure about any question, simply type a ? and I'll provide a brief explanation. You can also type 'example' or click the 'Example' button to see a sample response.\n\nLet's get started! Could you please provide your name and your company name?"
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
        st.session_state.visible_messages.append({"role": "assistant", "content": welcome_message})

    def save_session(self):
        """Save the current session state to cookies and optionally to a file."""
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
                    clean_visible_messages.append({"role": msg["role"], "content": msg["content"]})
            session_data["visible_messages"] = clean_visible_messages

            # Try to save to cookie
            cookie_success = False
            if self.cookies:
                try:
                    self.cookies[COOKIE_KEYS["SESSION"]] = json.dumps(session_data)
                    self.cookies.save()
                    if self.cookies.get(COOKIE_KEYS["SESSION"]):
                        cookie_success = True
                        return {"success": True, "method": "cookie", "message": "Session saved to browser cookie."}
                except Exception as e:
                    print(f"Cookie save error: {str(e)}")
            
            # Return serialized data for file download if cookie fails
            if not cookie_success:
                return {
                    "success": True, 
                    "method": "file", 
                    "message": "Cookie storage unavailable. Please download the file.",
                    "data": json.dumps(session_data)
                }
                
        except Exception as e:
            return {"success": False, "message": f"Error saving session: {str(e)}"}
    
    def restore_session(self, source="cookie", file_data=None):
        """
        Restore a saved session from cookie or file.
        
        Args:
            source: "cookie" or "file"
            file_data: JSON string data if source is "file"
            
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
            if source == "cookie" and self.cookies:
                cookie_data = self.cookies.get(COOKIE_KEYS["SESSION"])
                if cookie_data:
                    session_data = json.loads(cookie_data)
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
                
                # Add a special system message to inform the AI we're restoring a session
                session_timestamp = session_data.get("saved_timestamp", "previous session")
                restoration_message = {
                    "role": "system",
                    "content": f"""
                    IMPORTANT: This conversation is being resumed from a saved session from {session_timestamp}.
                    The user's name is {session_data['user_info'].get('name', 'unknown')} and they work for {session_data['user_info'].get('company', 'unknown company')}.
                    Continue the conversation naturally from where it left off without repeating questions.
                    
                    Topic areas already covered: {', '.join([TOPIC_AREAS[t] for t, v in session_data.get('topic_areas_covered', {}).items() if v])}
                    Topic areas still needed: {', '.join([TOPIC_AREAS[t] for t, v in session_data.get('topic_areas_covered', {}).items() if not v])}
                    
                    Current question index: {session_data['current_question_index']}
                    """
                }
                session_data["chat_history"].append(restoration_message)
                
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
            
            # Mark restoration as complete
            st.session_state.restoring_session = False
            
            return {"success": True, "message": f"Session restored from {source} successfully."}
            
        except Exception as e:
            st.session_state.restoring_session = False
            return {"success": False, "message": f"Error restoring session: {str(e)}"}
    
    def test_cookie(self, test_value="test_value"):
        """Set a test cookie to verify cookie functionality."""
        if not self.cookies:
            return {"success": False, "message": "Cookie manager not initialized."}
            
        try:
            self.cookies[COOKIE_KEYS["TEST"]] = test_value
            self.cookies.save()
            
            # Verify cookie was set
            if self.cookies.get(COOKIE_KEYS["TEST"]) == test_value:
                return {"success": True, "message": f"Test cookie set. Value: {test_value}"}
            else:
                return {"success": False, "message": "Failed to verify test cookie."}
        except Exception as e:
            return {"success": False, "message": f"Error setting test cookie: {str(e)}"}