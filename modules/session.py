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
        self.server_storage = ServerStorage()
        
    def get_session_state(self):
        """Return the current session state data structure."""
        if 'user_info' not in st.session_state:
            # This will call _initialize_session_state if called before app.py fully initializes.
            # It's better if app.py ensures initialization first.
            # For safety, we can call it, but app.py's explicit init is preferred.
            if not hasattr(st.session_state, 'initialized_by_app'):
                 self._initialize_session_state()

        return {
            "user_info": st.session_state.user_info,
            "responses": st.session_state.responses,
            "current_question_index": st.session_state.current_question_index,
            "chat_history": st.session_state.chat_history,
            "visible_messages": st.session_state.visible_messages,
            "topic_areas_covered": st.session_state.topic_areas_covered,
            "saved_timestamp": datetime.now().isoformat(),
            "version": "3.0"
        }
    
    def _initialize_session_state(self):
        """Initialize the session state with default values. The AI will generate the first message."""
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
            
        # Chat history will initially only contain the system prompt.
        # The AI will generate the first message based on instructions in app.py.
        st.session_state.chat_history = [{"role": "system", "content": st.session_state.instructions}]
        st.session_state.visible_messages = [] # Start with no visible messages
        
        st.session_state.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
        st.session_state.summary_requested = False
        st.session_state.explicitly_finished = False
        st.session_state.restoring_session = False
        
        # Flag that this specific initialization has run
        st.session_state.initialized_by_session_manager = True


    def save_session(self):
        """Save the current session state to server storage or file."""
        try:
            session_data = self.get_session_state()
            
            clean_chat_history = []
            for msg in session_data["chat_history"]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    clean_chat_history.append({"role": msg["role"], "content": str(msg["content"])}) # Ensure content is string
            session_data["chat_history"] = clean_chat_history
            
            clean_visible_messages = []
            for msg in session_data["visible_messages"]:
                if isinstance(msg, dict) and "role" in msg and "content" in msg:
                    clean_visible_messages.append({"role": msg["role"], "content": str(msg["content"])}) # Ensure content is string
            session_data["visible_messages"] = clean_visible_messages
            
            server_result = self.server_storage.save_session(session_data)
            server_success = server_result.get("success", False)
            session_id = server_result.get("session_id", "")
            
            if server_success:
                return {
                    "success": True,
                    "method": "server",
                    "message": "Session saved to server.",
                    "session_id": session_id
                }
            else:
                return {
                    "success": True, 
                    "method": "file", 
                    "message": "Server storage unavailable. Please download the file.",
                    "data": json.dumps(session_data)
                }
                
        except Exception as e:
            return {"success": False, "message": f"Error saving session: {str(e)}"}
    
    def restore_session(self, source="file", file_data=None, session_id=None):
        """Restore a saved session from server or file."""
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

            st.session_state.chat_history = session_data.get("chat_history", [{"role": "system", "content": st.session_state.instructions}])
            if not st.session_state.chat_history or st.session_state.chat_history[0].get("role") != "system":
                st.session_state.chat_history.insert(0, {"role": "system", "content": st.session_state.instructions})
            
            # Ensure all content in chat_history is string
            for msg in st.session_state.chat_history:
                if "content" in msg and msg["content"] is None:
                    msg["content"] = "" 
                elif "content" in msg and not isinstance(msg["content"], str):
                    msg["content"] = str(msg["content"])


            current_q_index = st.session_state.current_question_index
            current_q = st.session_state.current_question
            topics_covered_state = session_data.get('topic_areas_covered', {})
            topics_covered_str = ', '.join([TOPIC_AREAS.get(t, t) for t, v in topics_covered_state.items() if v]) or "None yet"
            topics_needed_str = ', '.join([TOPIC_AREAS.get(t,t) for t, v in topics_covered_state.items() if not v]) or "All seem covered, but please verify."

            restoration_context_content = (
                "[SYSTEM_INSTRUCTION_FOR_THIS_TURN]:\n"
                "CRITICAL CONTEXT RESTORATION:\n"
                "1. This conversation is being resumed from a previous session.\n"
                f"2. User name: {st.session_state.user_info.get('name', 'unknown')}\n"
                f"3. Company: {st.session_state.user_info.get('company', 'unknown company')}\n"
                f"4. Current question index: {current_q_index}\n"
                f"5. The last question asked or being discussed was related to: {current_q}\n"
                f"6. Last active timestamp: {session_data.get('saved_timestamp', 'unknown')}\n"
                f"7. Topics already covered in detail: {topics_covered_str}\n"
                f"8. Topics still needing focus: {topics_needed_str}\n\n"
                "YOUR TASK NOW:\n"
                "- Acknowledge that the conversation is being resumed.\n"
                "- Briefly (1 sentence) remind the user of the last question or topic we were on.\n"
                "- Then, ask the next logical question based on the current_question_index and topics_needed_str, or if all topics seem covered, confirm with the user.\n"
                "- Continue the conversation naturally. DO NOT repeat questions already clearly answered.\n"
                "- Maintain a friendly, conversational tone.\n"
                "[END_SYSTEM_INSTRUCTION]"
            )
            st.session_state.chat_history.append({
                 "role": "system",
                 "content": restoration_context_content
            })
            
            st.session_state.visible_messages = session_data.get("visible_messages", [])
            # Ensure all content in visible_messages is string
            for msg in st.session_state.visible_messages:
                if "content" in msg and msg["content"] is None:
                    msg["content"] = ""
                elif "content" in msg and not isinstance(msg["content"], str):
                     msg["content"] = str(msg["content"])

            st.session_state.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
            saved_topics = session_data.get("topic_areas_covered", {})
            for topic, covered in saved_topics.items():
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = covered
            
            st.session_state.summary_requested = session_data.get("summary_requested", False)
            st.session_state.explicitly_finished = session_data.get("explicitly_finished", False)
            
            st.session_state.restoring_session = False 
            
            return {"success": True, "message": f"Session restored from {source}. The assistant will now welcome you back."}
            
        except Exception as e:
            st.session_state.restoring_session = False
            import traceback
            print(f"Error restoring session: {str(e)}\n{traceback.format_exc()}")
            return {"success": False, "message": f"Error restoring session: {str(e)}"}