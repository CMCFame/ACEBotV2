# modules/session.py
import json
import time
import streamlit as st
from datetime import datetime
import os
from cryptography.fernet import Fernet
import base64

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
        def save_encrypted_session(self, encrypted_data):
            return {"success": False, "message": "Server storage not available"}
        def load_encrypted_session(self, session_id):
            return {"success": False, "message": "Server storage not available"}

class SessionManager:
    def __init__(self):
        """Initialize the session manager with HIPAA-compliant encryption."""
        # Initialize with encryption key from environment or secrets
        self.encryption_key = os.environ.get('ENCRYPTION_KEY') or st.secrets.get("ENCRYPTION_KEY")
        if not self.encryption_key:
            # Generate a key if not present - WARNING: This is not ideal for production
            # as sessions encrypted with this key will not be accessible after restart
            self.encryption_key = Fernet.generate_key().decode()
            print(f"WARNING: No encryption key found in environment. Generated temporary key.")
            print("Store this key securely for future sessions in the ENCRYPTION_KEY environment variable.")
        
        # Initialize Fernet cipher suite for encryption
        self.cipher_suite = Fernet(self.encryption_key.encode() if isinstance(self.encryption_key, str) else self.encryption_key)
        
        # Initialize server storage
        self.server_storage = ServerStorage()
        
        # Set timeout for inactive sessions (in minutes)
        self.session_timeout = 30  # HIPAA requirement: automatically log off after period of inactivity
        
        # Track last activity time
        if 'last_activity' not in st.session_state:
            st.session_state.last_activity = datetime.now()
    
    def get_session_state(self):
        """Return the current session state data structure."""
        if 'user_info' not in st.session_state:
            self._initialize_session_state()
            
        # Update last activity timestamp
        st.session_state.last_activity = datetime.now()
            
        return {
            "user_info": st.session_state.user_info,
            "responses": st.session_state.responses,
            "current_question_index": st.session_state.current_question_index,
            "chat_history": st.session_state.chat_history,
            "visible_messages": st.session_state.visible_messages,
            "topic_areas_covered": st.session_state.topic_areas_covered,
            "saved_timestamp": datetime.now().isoformat(),
            "version": "4.0",  # Updated version for HIPAA compliance
            "last_activity": st.session_state.last_activity.isoformat()
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
        
        # Set up session security properties
        st.session_state.session_id = self._generate_secure_id()
        st.session_state.last_activity = datetime.now()
        
        # Add HIPAA compliance notice to chat history
        hipaa_notice = {"role": "system", "content": "This conversation is protected under HIPAA regulations. All activity is logged and monitored for security purposes."}
        st.session_state.chat_history.append(hipaa_notice)
        
        # Add initial greeting that includes the first question
        welcome_message = "👋 Hello! This questionnaire is designed to help ARCOS solution consultants better understand your company's requirements. If you're unsure about any question, simply type a ? and I'll provide a brief explanation. You can also type 'example' or click the 'Example' button to see a sample response.\n\nLet's get started! Could you please provide your name and your company name?"
        st.session_state.chat_history.append({"role": "assistant", "content": welcome_message})
        st.session_state.visible_messages.append({"role": "assistant", "content": welcome_message})
    
    def _generate_secure_id(self):
        """Generate a cryptographically secure session ID."""
        import uuid
        return str(uuid.uuid4())
    
    def check_session_timeout(self):
        """Check if the session has timed out due to inactivity."""
        if 'last_activity' not in st.session_state:
            return False
            
        last_activity = st.session_state.last_activity
        if isinstance(last_activity, str):
            try:
                last_activity = datetime.fromisoformat(last_activity)
            except ValueError:
                return False  # Could not parse timestamp
        
        # Calculate time difference in minutes
        elapsed_minutes = (datetime.now() - last_activity).total_seconds() / 60
        
        # Check if session timeout reached
        return elapsed_minutes >= self.session_timeout

    def save_session(self):
        """Save the current session state to server storage or file with encryption."""
        try:
            # Check for session timeout
            if self.check_session_timeout():
                return {
                    "success": False, 
                    "message": f"Session timed out after {self.session_timeout} minutes of inactivity. Please log in again."
                }
            
            # Update last activity timestamp
            st.session_state.last_activity = datetime.now()
            
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
            
            # Add audit data for HIPAA compliance
            session_data["_audit"] = {
                "saved_by": st.session_state.get("user", {}).get("username", "anonymous"),
                "saved_at": datetime.now().isoformat(),
                "ip_address": self._get_client_ip()
            }
            
            # Encrypt the data
            json_data = json.dumps(session_data)
            encrypted_data = self.cipher_suite.encrypt(json_data.encode())
            
            # Try to save to server storage (primary method)
            server_result = self.server_storage.save_encrypted_session(encrypted_data)
            server_success = server_result.get("success", False)
            session_id = server_result.get("session_id", "")
            
            # Log session save attempt
            self._log_session_activity("save_session", session_id, server_success)
            
            # Return the result
            if server_success:
                return {
                    "success": True,
                    "method": "server",
                    "message": "Session saved to server with encryption.",
                    "session_id": session_id
                }
            else:
                # Return encrypted data for file download as fallback
                return {
                    "success": True, 
                    "method": "file", 
                    "message": "Server storage unavailable. Please download the encrypted file.",
                    "data": base64.b64encode(encrypted_data).decode()
                }
                
        except Exception as e:
            self._log_session_activity("save_session_error", "", False, str(e))
            return {"success": False, "message": f"Error saving session: {str(e)}"}
    
    def restore_session(self, source="file", file_data=None, session_id=None):
        """
        Restore a saved session from server or file with decryption.
        
        Args:
            source: "server" or "file"
            file_data: Base64 encoded encrypted data if source is "file"
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
            
            # Get encrypted session data from source
            encrypted_data = None
            if source == "server" and session_id:
                server_result = self.server_storage.load_encrypted_session(session_id)
                if server_result.get("success", False):
                    encrypted_data = server_result.get("encrypted_data")
            elif source == "file" and file_data:
                try:
                    encrypted_data = base64.b64decode(file_data)
                except:
                    st.session_state.restoring_session = False
                    self._log_session_activity("restore_session_error", session_id, False, "Invalid file format")
                    return {"success": False, "message": "Invalid file format or encryption."}
            
            if not encrypted_data:
                st.session_state.restoring_session = False
                self._log_session_activity("restore_session_error", session_id, False, "No saved session found")
                return {"success": False, "message": f"No saved session found in {source}."}
            
            # Decrypt the data
            try:
                decrypted_data = self.cipher_suite.decrypt(encrypted_data).decode()
                session_data = json.loads(decrypted_data)
            except Exception as e:
                st.session_state.restoring_session = False
                self._log_session_activity("restore_session_error", session_id, False, f"Decryption error: {str(e)}")
                return {"success": False, "message": f"Error decrypting session data. This could be due to an incorrect encryption key or corrupted data."}
            
            # Check session format version
            if "version" not in session_data:
                # Handle legacy format
                print("Legacy session format detected, attempting conversion")
            
            # Add restore audit data
            session_data["_audit_restore"] = {
                "restored_by": st.session_state.get("user", {}).get("username", "anonymous"),
                "restored_at": datetime.now().isoformat(),
                "ip_address": self._get_client_ip(),
                "original_session_id": session_id
            }
            
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
                
                # Create a much more detailed context restoration message
                current_q_index = session_data.get('current_question_index', 0)
                current_q = st.session_state.questions[min(current_q_index, len(st.session_state.questions)-1)]
                
                # Enhanced context restoration to help the AI understand exactly where we left off
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
                    7. This session is protected under HIPAA regulations. All activity is logged.
                    
                    Topics already covered in detail:
                    {', '.join([TOPIC_AREAS[t] for t, v in session_data.get('topic_areas_covered', {}).items() if v])}
                    
                    Topics still needed:
                    {', '.join([TOPIC_AREAS[t] for t, v in session_data.get('topic_areas_covered', {}).items() if not v])}
                    
                    YOU MUST:
                    - Continue the conversation naturally from where it left off
                    - DO NOT repeat questions that have already been asked
                    - FOCUS on gathering information about missing topics
                    - Acknowledge that the conversation is being resumed
                    - Maintain a friendly, conversational tone
                    - If the user seems confused, briefly remind them where you were in the conversation
                    - If you want to summarize what you've learned so far to help reestablish context, do so BRIEFLY (1-2 sentences max)
                    - Respect any previous statements about skipping certain questions or topics
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
                
                # Add HIPAA compliance notice
                hipaa_notice = {"role": "system", "content": "This conversation is protected under HIPAA regulations. All activity is logged and monitored for security purposes."}
                st.session_state.chat_history.append(hipaa_notice)
            
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
            
            # Update session security data
            st.session_state.session_id = session_id or self._generate_secure_id()
            st.session_state.last_activity = datetime.now()
            
            # Add a visible message informing the user that the session was restored
            st.session_state.visible_messages.append({
                "role": "assistant", 
                "content": f"👋 Welcome back! I've restored your previous session. We were discussing {current_q}. Let's continue from where we left off."
            })
            
            # Log successful restoration
            self._log_session_activity("restore_session", st.session_state.session_id, True)
            
            # Mark restoration as complete
            st.session_state.restoring_session = False
            
            return {"success": True, "message": f"Session restored from {source} successfully."}
            
        except Exception as e:
            st.session_state.restoring_session = False
            self._log_session_activity("restore_session_error", session_id, False, str(e))
            return {"success": False, "message": f"Error restoring session: {str(e)}"}
    
    def _get_client_ip(self):
        """Get the client's IP address for audit logging."""
        # In production, this should extract the IP from request headers
        # This is a placeholder implementation
        return "127.0.0.1"
    
    def _log_session_activity(self, action_type, session_id, success, error_message=None):
        """Log session activity for HIPAA audit purposes."""
        try:
            # Ensure log directory exists
            log_dir = "secure/session_logs"
            os.makedirs(log_dir, exist_ok=True)
            
            # Create log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "action": action_type,
                "session_id": session_id,
                "user": st.session_state.get("user", {}).get("username", "anonymous"),
                "ip_address": self._get_client_ip(),
                "success": success
            }
            
            # Add error message if present
            if error_message:
                log_entry["error"] = error_message
            
            # Write to log file
            log_file = os.path.join(log_dir, f"session_log_{datetime.now().strftime('%Y-%m-%d')}.jsonl")
            with open(log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
                
            return True
        except Exception as e:
            print(f"Error logging session activity: {e}")
            return False
    
    def redact_phi(self, session_data):
        """Create a redacted copy of session data with PHI removed for export."""
        # Create a deep copy to avoid modifying the original
        import copy
        redacted_data = copy.deepcopy(session_data)
        
        # Simple PHI patterns
        phi_patterns = {
            r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b': '[REDACTED SSN]',  # SSN
            r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b': '[REDACTED PHONE]',  # Phone
            r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b': '[REDACTED EMAIL]',  # Email
            r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Highway|Hwy|Square|Sq|Trail|Trl|Drive|Dr|Court|Ct|Park|Parkway|Pkwy|Circle|Cir|Boulevard|Blvd)\b': '[REDACTED ADDRESS]',  # Address
            r'\b(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])[\/\-](19|20)\d{2}\b': '[REDACTED DATE]'  # Date
        }
        
        import re
        
        # Function to redact text
        def redact_text(text):
            if not isinstance(text, str):
                return text
                
            for pattern, replacement in phi_patterns.items():
                text = re.sub(pattern, replacement, text)
            return text
        
        # Redact user info
        if "user_info" in redacted_data:
            redacted_data["user_info"]["name"] = redact_text(redacted_data["user_info"].get("name", ""))
            redacted_data["user_info"]["company"] = redact_text(redacted_data["user_info"].get("company", ""))
        
        # Redact responses
        if "responses" in redacted_data:
            for i, (question, answer) in enumerate(redacted_data["responses"]):
                redacted_data["responses"][i] = (question, redact_text(answer))
        
        # Redact chat history
        if "chat_history" in redacted_data:
            for i, message in enumerate(redacted_data["chat_history"]):
                if message.get("role") == "user":
                    redacted_data["chat_history"][i]["content"] = redact_text(message.get("content", ""))
        
        # Redact visible messages
        if "visible_messages" in redacted_data:
            for i, message in enumerate(redacted_data["visible_messages"]):
                if message.get("role") == "user":
                    redacted_data["visible_messages"][i]["content"] = redact_text(message.get("content", ""))
        
        # Add redaction metadata
        redacted_data["_redacted"] = {
            "timestamp": datetime.now().isoformat(),
            "redacted_by": st.session_state.get("user", {}).get("username", "system"),
            "reason": "PHI protection",
            "phi_patterns_count": len(phi_patterns)
        }
        
        return redacted_data
    
    def create_anonymized_export(self):
        """Create an anonymized export of the session data for research or analysis."""
        session_data = self.get_session_state()
        
        # Create anonymized copy
        anon_data = {
            "session_id": self._generate_secure_id(),  # New random ID
            "created_at": datetime.now().isoformat(),
            "topics_covered": {},
            "question_count": len(st.session_state.questions),
            "responses_count": len(session_data.get("responses", [])),
            "completion_percentage": 0,
            "questions_by_topic": {}
        }
        
        # Calculate topic coverage
        for topic, covered in session_data.get("topic_areas_covered", {}).items():
            anon_data["topics_covered"][topic] = covered
            
        # Calculate completion percentage
        if "topic_areas_covered" in session_data:
            covered_count = sum(1 for v in session_data["topic_areas_covered"].values() if v)
            total_count = len(session_data["topic_areas_covered"])
            if total_count > 0:
                anon_data["completion_percentage"] = int((covered_count / total_count) * 100)
                
        # Add anonymous question data (just the count by topic, not the answers)
        topic_counts = {}
        for response in session_data.get("responses", []):
            question = response[0]
            # You'd need a way to map questions to topics here
            # This is just a simplified example
            topic = "unknown"
            if topic not in topic_counts:
                topic_counts[topic] = 0
            topic_counts[topic] += 1
            
        anon_data["questions_by_topic"] = topic_counts
        
        return anon_data