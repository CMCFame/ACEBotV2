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
            "version": "3.1"  # Updated version for improved session handling
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
        welcome_message = ("👋 Hello! This questionnaire is designed to help ARCOS solution consultants better understand your company's requirements. "
                          "If you're unsure about any question, simply type a ? and I'll provide a brief explanation. You can also type 'example' or click the 'Example' button to see a sample response.\n\n"
                          "Let's get started! Could you please provide your name and your company name?")
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
                    clean_msg = {
                        "role": str(msg["role"]),
                        "content": str(msg["content"]) if msg["content"] is not None else ""
                    }
                    clean_chat_history.append(clean_msg)
            session_data["chat_history"] = clean_chat_history
            
            # Clean up visible messages
            clean_visible_messages = []
            for msg in session_data["visible_messages"]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    clean_msg = {
                        "role": str(msg["role"]),
                        "content": str(msg["content"]) if msg["content"] is not None else ""
                    }
                    clean_visible_messages.append(clean_msg)
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
                    "data": json.dumps(session_data, indent=2)
                }
                
        except Exception as e:
            print(f"Error in save_session: {e}")
            return {"success": False, "message": f"Error saving session: {str(e)}"}
    
    def restore_session(self, source="file", file_data=None, session_id=None):
        """
        Restore a saved session from server or file.
        
        Args:
            source: "server" or "file"
            file_data: JSON string data if source is "file"
            session_id: Session ID if source is "server"
            
        Returns:
            dict: Result of the operation
        """
        try:
            if st.session_state.get("restoring_session", False):
                return {"success": False, "message": "Already restoring a session."}
            
            st.session_state.restoring_session = True
            
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
            
            # Basic session state restoration
            st.session_state.user_info = session_data.get("user_info", {"name": "", "company": ""})
            st.session_state.responses = session_data.get("responses", [])
            st.session_state.current_question_index = session_data.get("current_question_index", 0)

            if 'questions' not in st.session_state:
                from utils.helpers import load_questions
                st.session_state.questions = load_questions('data/questions.txt')
            
            if st.session_state.current_question_index < len(st.session_state.questions):
                st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]
            else:
                st.session_state.current_question_index = 0
                st.session_state.current_question = st.session_state.questions[0]

            if 'instructions' not in st.session_state:
                from utils.helpers import load_instructions
                st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')

            # Restore chat history with validation
            saved_chat_history = session_data.get("chat_history", [])
            st.session_state.chat_history = []
            
            # Ensure system prompt is first
            if not saved_chat_history or saved_chat_history[0].get("role") != "system":
                st.session_state.chat_history.append({"role": "system", "content": st.session_state.instructions})
            
            # Add saved messages with validation
            for msg in saved_chat_history:
                if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
                    clean_msg = {
                        "role": str(msg["role"]),
                        "content": str(msg["content"])
                    }
                    st.session_state.chat_history.append(clean_msg)

            # Restore visible messages with validation
            saved_visible_messages = session_data.get("visible_messages", [])
            st.session_state.visible_messages = []
            
            for msg in saved_visible_messages:
                if isinstance(msg, dict) and msg.get("role") and msg.get("content"):
                    clean_msg = {
                        "role": str(msg["role"]),
                        "content": str(msg["content"])
                    }
                    st.session_state.visible_messages.append(clean_msg)
            
            # Restore topic tracking
            st.session_state.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
            saved_topics = session_data.get("topic_areas_covered", {})
            for topic, covered in saved_topics.items():
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = bool(covered)
            
            st.session_state.summary_requested = session_data.get("summary_requested", False)
            st.session_state.explicitly_finished = session_data.get("explicitly_finished", False)
            
            # Add a simple welcome back message to visible messages
            user_name = st.session_state.user_info.get("name", "")
            welcome_back_msg = f"Welcome back{', ' + user_name if user_name else ''}! I've restored your previous session. Let's continue where we left off."
            
            st.session_state.visible_messages.append({
                "role": "assistant",
                "content": welcome_back_msg
            })
            
            # Also add to chat history for AI context
            st.session_state.chat_history.append({
                "role": "assistant",
                "content": welcome_back_msg
            })

            st.session_state.restoring_session = False 
            
            return {"success": True, "message": f"Session restored from {source}. Welcome back!"}
            
        except Exception as e:
            st.session_state.restoring_session = False
            # Print detailed error for debugging
            import traceback
            print(f"Error restoring session: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": f"Error restoring session: {str(e)}"}