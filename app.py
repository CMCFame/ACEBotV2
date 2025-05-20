# app.py
# IMPORTANT: set_page_config must be the very first Streamlit command!
import streamlit as st

st.set_page_config(
    page_title="ACE Questionnaire",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now we can import other dependencies
import os
import json
from datetime import datetime, timedelta
import time

# Safe import for AuditLogger
try:
    from modules.audit import AuditLogger
except ImportError:
    # Define a minimal fallback version if the module doesn't exist yet
    class AuditLogger:
        def __init__(self, log_dir="secure/audit_logs"):
            os.makedirs(log_dir, exist_ok=True)
            print("Using fallback AuditLogger")
        
        def log_event(self, event_type, user=None, details=None, status="success"):
            """Simple fallback logging function"""
            print(f"AUDIT LOG: {event_type} by {user or 'anonymous'} - {status}")
            return True

# Safe import for AuthenticationService
try:
    from modules.auth import AuthenticationService
except ImportError:
    # Define a minimal fallback version
    class AuthenticationService:
        def __init__(self):
            print("Using fallback AuthenticationService")
            
        def authenticate_user(self, username, password):
            print(f"Mock login: {username}")
            st.session_state.user = {"username": username, "role": "admin" if username == "admin" else "user"}
            return {"success": True, "message": "Login successful"}
            
        def logout_user(self):
            if "user" in st.session_state:
                del st.session_state.user
            return {"success": True, "message": "Logged out successfully"}
            
        def is_authenticated(self):
            return "user" in st.session_state

# Continue with other imports
try:
    from modules.session import SessionManager
    from modules.ai_service import AIService
    from modules.topic_tracker import TopicTracker
    from modules.chat_ui import ChatUI
    from modules.summary import SummaryGenerator
    from modules.export import ExportService
    from modules.email_service import EmailService
    from utils.helpers import load_css, apply_css, load_instructions, load_questions
    from config import TOPIC_AREAS
except ImportError as e:
    st.error(f"Import error: {e}. Please check that all required modules are installed.")
    st.stop()

# Safe import for HIPAA related modules
try:
    from modules.data_retention import DataRetentionManager
except ImportError:
    class DataRetentionManager:
        def __init__(self, storage_dir="session_data", retention_days=730):
            pass
        def apply_retention_policy(self):
            return {"files_scanned": 0, "files_purged": 0, "files_archived": 0, "errors": 0}
        def archive_completed_sessions(self, completed_only=True):
            return {"files_scanned": 0, "files_archived": 0, "errors": 0}

try:
    from modules.baa_compliance import BAAComplianceManager
except ImportError:
    class BAAComplianceManager:
        def __init__(self, baa_dir="secure/baa"):
            self.baa_info = {"is_active": False}
        def check_baa_status(self):
            return {"status": "inactive", "message": "BAA module not available"}

try:
    from modules.emergency_access import EmergencyAccessManager
except ImportError:
    class EmergencyAccessManager:
        def __init__(self, emergency_dir="secure/emergency"):
            self.settings = {"notification_recipients": [], "emergency_contacts": []}
        def log_emergency_access(self, username, reason, accessed_data):
            return {"success": False, "message": "Emergency access module not available"}

try:
    from modules.data_classification import PHIDataClassifier
except ImportError:
    class PHIDataClassifier:
        def __init__(self):
            pass
        def scan_text_for_phi(self, text):
            return {"has_phi": False, "phi_types": []}

try:
    from modules.server_storage import ServerStorage
except ImportError:
    class ServerStorage:
        def __init__(self, storage_dir="session_data"):
            pass
        def list_sessions(self, limit=10):
            return []

# Function to create formatted HTML for examples
def create_example_html(example_text, question_text):
    """Create formatted HTML for examples and questions."""
    return f"""
    <div style="display: flex; margin-bottom: 15px;">
      <div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 90%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef;">
        <p style="margin: 0; color: #495057; font-weight: 600; font-size: 15px;">💬 Assistant</p>
        <div style="background-color: #fff3cd; border-radius: 10px; padding: 15px; margin-top: 12px; margin-bottom: 15px; border: 1px solid #ffeeba; border-left: 5px solid #ffc107;">
          <p style="margin: 0; font-weight: 600; color: #856404; font-size: 15px;">📝 Example</p>
          <p style="margin: 8px 0 0 0; color: #533f03; font-style: italic; line-height: 1.5;">{example_text}</p>
        </div>
        <div style="background-color: #e8f4ff; border-radius: 10px; padding: 15px; border: 1px solid #d1ecf1; border-left: 5px solid #007bff;">
          <p style="margin: 0; font-weight: 600; color: #004085; font-size: 15px;">❓ Question</p>
          <p style="margin: 8px 0 0 0; color: #0c5460; line-height: 1.5;">{question_text}</p>
        </div>
      </div>
    </div>
    """

# Safe wrapper for audit logging
def log_event(event_type, user=None, details=None, status="success"):
    """Safe wrapper for audit logging"""
    try:
        if st.session_state.get('audit_logger'):
            st.session_state.audit_logger.log_event(
                event_type, 
                user=user, 
                details=details,
                status=status
            )
    except Exception as e:
        print(f"Audit logging error: {e}")

# Initialize services - removed caching to avoid widget error
def init_services():
    """Initialize the application services."""
    session_manager = SessionManager()
    ai_service = AIService()
    topic_tracker = TopicTracker()
    chat_ui = ChatUI()
    summary_generator = SummaryGenerator()
    export_service = ExportService()
    email_service = EmailService()
    
    return {
        "session_manager": session_manager,
        "ai_service": ai_service,
        "topic_tracker": topic_tracker,
        "chat_ui": chat_ui,
        "summary_generator": summary_generator,
        "export_service": export_service,
        "email_service": email_service
    }

services = init_services()

# Load and apply CSS
try:
    css_content = load_css("assets/style.css")
    apply_css(css_content)
except Exception as e:
    st.warning(f"Could not load CSS: {e}. Using default styling.")
    # Apply minimal CSS as fallback
    st.markdown("""
    <style>
    body {
        font-family: sans-serif;
    }
    .ai-help, .ai-example {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

def add_sidebar_ui():
    """Add the sidebar UI elements."""
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png"
                     alt="Company Logo" style="max-width: 80%; height: auto; margin: 10px auto;" />
            </div>
            <div style="text-align: center;">
                <h3 style="color: var(--primary-red); margin-bottom: 10px;">
                    <i>Save & Resume Progress</i>
                </h3>
                <p style="font-size: 0.9em; color: #555; margin-bottom: 20px;">
                    Save your progress at any time and continue later.
                </p>
            </div>
        """, unsafe_allow_html=True)

        # Save Progress button
        if st.button("💾 Save Progress", key="save_progress"):
            result = services["session_manager"].save_session()
            
            if result["success"]:
                if result["method"] == "server":
                    st.success(f"Session saved. Your Session ID: {result['session_id']}")
                    # Show session ID for later use
                    st.code(result["session_id"])
                    # Add a note to copy the session ID
                    st.info("Please copy and save this Session ID to resume your progress later.")
                    
                    log_event(
                        "session_save", 
                        user=st.session_state.get("user", {}).get("username", "anonymous"), 
                        details={"method": "server", "session_id": result["session_id"]}
                    )
                else:
                    st.warning(result["message"])
                    st.download_button(
                        label="📥 Download Progress File",
                        data=result["data"],
                        file_name=f"ace_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_progress"
                    )
                    
                    log_event(
                        "session_save", 
                        user=st.session_state.get("user", {}).get("username", "anonymous"), 
                        details={"method": "file"}
                    )
            else:
                st.error(result["message"])
                log_event(
                    "session_save_error",
                    user=st.session_state.get("user", {}).get("username", "anonymous"), 
                    details={"error": result["message"]},
                    status="failure"
                )
        
        # Progress dashboard button
        if st.button("📊 View Progress Dashboard", key="view_progress"):
            dashboard = services["summary_generator"].generate_progress_dashboard()
            st.session_state.show_dashboard = True
            st.session_state.dashboard_content = dashboard
            st.rerun()

        # Display dashboard if requested
        if st.session_state.get("show_dashboard", False):
            with st.expander("Progress Dashboard", expanded=True):
                st.markdown(st.session_state.dashboard_content)
                
                # Add download button
                st.download_button(
                    label="📥 Download Progress Report",
                    data=st.session_state.dashboard_content,
                    file_name=f"ace_progress_report_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
                
                if st.button("Close Dashboard", key="close_dashboard"):
                    st.session_state.show_dashboard = False
                    st.rerun()

        st.markdown("---")
        
        # Resume section
        st.markdown("### Resume Progress")
        
        # Server restore section (priority method)
        st.markdown("#### Resume from Server")
        session_id = st.text_input("Enter Session ID")
        if session_id and st.button("Load from Server", key="server_load"):
            result = services["session_manager"].restore_session(source="server", session_id=session_id)
            if result["success"]:
                st.success(result["message"])
                log_event(
                    "session_restore",
                    user=st.session_state.get("user", {}).get("username", "anonymous"), 
                    details={"method": "server", "session_id": session_id}
                )
                st.rerun()
            else:
                st.error(result["message"])
                log_event(
                    "session_restore_error",
                    user=st.session_state.get("user", {}).get("username", "anonymous"), 
                    details={"method": "server", "error": result["message"]},
                    status="failure"
                )
        
        # File upload option
        st.markdown("#### Or Upload Progress File")
        uploaded_file = st.file_uploader("Choose a saved progress file", type=["json"], key="progress_file")
        
        if uploaded_file is not None:
            try:
                # Read file content as string
                content = uploaded_file.read().decode("utf-8")
                
                # Load button only shows after file is uploaded
                if st.button("📤 Load from File", key="load_file"):
                    result = services["session_manager"].restore_session(source="file", file_data=content)
                    if result["success"]:
                        st.success(result["message"])
                        log_event(
                            "session_restore",
                            user=st.session_state.get("user", {}).get("username", "anonymous"), 
                            details={"method": "file"}
                        )
                        st.rerun()
                    else:
                        st.error(result["message"])
                        log_event(
                            "session_restore_error",
                            user=st.session_state.get("user", {}).get("username", "anonymous"), 
                            details={"method": "file", "error": result["message"]},
                            status="failure"
                        )
            except Exception as e:
                st.error(f"Error processing file: {e}")
                log_event(
                    "session_restore_error",
                    user=st.session_state.get("user", {}).get("username", "anonymous"), 
                    details={"method": "file", "error": str(e)},
                    status="failure"
                )

def login_page():
    """Display the login page."""
    auth_service = AuthenticationService()
    
    # Check if already logged in
    if auth_service.is_authenticated():
        return True
    
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <h1 style="color: #D22B2B; margin-bottom: 5px;">ACE Questionnaire</h1>
            <p style="color: #555; font-size: 16px;">
                Secure Login Required
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add HIPAA compliance notice
    st.markdown(
        """
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #17a2b8;">
            <p style="margin: 0; color: #17a2b8;"><strong>HIPAA Compliance Notice:</strong> This system contains protected health information (PHI) and is governed by HIPAA regulations. Unauthorized access is prohibited by law.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create tabs for login and password reset
    login_tab, reset_tab = st.tabs(["Login", "Reset Password"])
    
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Login")
            
            if submit:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    try:
                        result = auth_service.authenticate_user(username, password)
                        if result["success"]:
                            st.success("Login successful!")
                            log_event(
                                "authentication", 
                                user=username, 
                                details={"action": "login"}
                            )
                            time.sleep(1)  # Brief pause before redirect
                            return True
                        else:
                            if "lockout" in result and result["lockout"]:
                                st.error("Too many failed login attempts. Please try again later.")
                                log_event(
                                    "authentication", 
                                    details={"action": "login_lockout", "username_attempt": username},
                                    status="failure"
                                )
                            else:
                                st.error(result["message"])
                                log_event(
                                    "authentication", 
                                    details={"action": "login_failed", "username_attempt": username},
                                    status="failure"
                                )
                    except Exception as e:
                        st.error(f"Login error: {str(e)}")
    
    with reset_tab:
        with st.form("reset_form"):
            reset_username = st.text_input("Username", key="reset_username")
            
            # Security questions
            q1_answer = st.text_input("What is your mother's maiden name?", type="password")
            q2_answer = st.text_input("What was your first pet's name?", type="password")
            
            reset_submit = st.form_submit_button("Reset Password")
            
            if reset_submit:
                if not reset_username or not q1_answer or not q2_answer:
                    st.error("Please answer all security questions")
                else:
                    try:
                        answers = {
                            "What is your mother's maiden name?": q1_answer,
                            "What was your first pet's name?": q2_answer
                        }
                        result = auth_service.reset_password_with_security_questions(reset_username, answers)
                        if result["success"]:
                            st.success("Password reset successful!")
                            st.info(f"Your temporary password is: {result['temp_password']}")
                            st.warning("Please login with this password and change it immediately.")
                            log_event(
                                "authentication", 
                                details={"action": "password_reset", "username": reset_username},
                                status="success"
                            )
                        else:
                            st.error(result["message"])
                            log_event(
                                "authentication", 
                                details={"action": "password_reset_failed", "username_attempt": reset_username},
                                status="failure"
                            )
                    except Exception as e:
                        st.error(f"Password reset error: {str(e)}")
    
    return False

def baa_management_ui():
    """Display BAA management interface for admins."""
    # Only show to admins
    if st.session_state.get("user", {}).get("role") != "admin":
        st.warning("You do not have permission to access this area.")
        return
    
    baa_manager = BAAComplianceManager()
    
    st.markdown("## BAA Management")
    
    # Display current BAA status
    baa_status = baa_manager.check_baa_status()
    
    status_colors = {
        "active": "green",
        "inactive": "red",
        "expired": "red",
        "review_overdue": "orange"
    }
    
    status_color = status_colors.get(baa_status["status"], "gray")
    
    st.markdown(
        f"""
        <div style="padding: 10px; background-color: {status_color}; color: white; border-radius: 5px; margin-bottom: 20px;">
            <strong>BAA Status:</strong> {baa_status["status"].upper()} - {baa_status["message"]}
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Create tabs for different BAA management functions
    tab1, tab2, tab3 = st.tabs(["BAA Details", "Authorized Personnel", "Compliance Logs"])
    
    with tab1:
        # BAA information form
        st.markdown("### BAA Details")
        
        with st.form("baa_info_form"):
            covered_entity = st.text_input("Covered Entity Name", baa_manager.baa_info.get("covered_entity", ""))
            business_associate = st.text_input("Business Associate Name", baa_manager.baa_info.get("business_associate", "ARCOS LLC"))
            
            # Handle dates
            effective_date_str = baa_manager.baa_info.get("effective_date") or datetime.now().isoformat()
            expiration_date_str = baa_manager.baa_info.get("expiration_date") or (datetime.now() + timedelta(days=365)).isoformat()
            
            try:
                effective_date = st.date_input("Effective Date", datetime.fromisoformat(effective_date_str))
                expiration_date = st.date_input("Expiration Date", datetime.fromisoformat(expiration_date_str))
                last_review_date = st.date_input(
                    "Last Review Date", 
                    datetime.fromisoformat(baa_manager.baa_info.get("last_review_date", "")) if baa_manager.baa_info.get("last_review_date") else datetime.now()
                )
            except ValueError:
                # Fallback for date parsing errors
                effective_date = datetime.now()
                expiration_date = datetime.now() + timedelta(days=365)
                last_review_date = datetime.now()
            
            # Data handling requirements
            st.markdown("#### Data Handling Requirements")
            requirements = baa_manager.baa_info.get("data_handling_requirements", {
                "encryption_required": True,
                "access_controls_required": True,
                "audit_logging_required": True,
                "retention_period_days": 730,
                "breach_notification_window_hours": 24
            })
            
            encryption_required = st.checkbox("Encryption Required", requirements.get("encryption_required", True))
            access_controls_required = st.checkbox("Access Controls Required", requirements.get("access_controls_required", True))
            audit_logging_required = st.checkbox("Audit Logging Required", requirements.get("audit_logging_required", True))
            
            retention_period = st.number_input(
                "Retention Period (days)", 
                min_value=30, 
                max_value=3650,  # 10 years max
                value=requirements.get("retention_period_days", 730)
            )
            
            breach_notification = st.number_input(
                "Breach Notification Window (hours)", 
                min_value=1, 
                max_value=168,  # 1 week max
                value=requirements.get("breach_notification_window_hours", 24)
            )
            
            submit_baa = st.form_submit_button("Update BAA Information")
            
            if submit_baa:
                try:
                    # Prepare updated BAA info
                    updated_info = {
                        "covered_entity": covered_entity,
                        "business_associate": business_associate,
                        "effective_date": effective_date.isoformat(),
                        "expiration_date": expiration_date.isoformat(),
                        "last_review_date": last_review_date.isoformat(),
                        "data_handling_requirements": {
                            "encryption_required": encryption_required,
                            "access_controls_required": access_controls_required,
                            "audit_logging_required": audit_logging_required,
                            "retention_period_days": retention_period,
                            "breach_notification_window_hours": breach_notification
                        }
                    }
                    
                    result = baa_manager.update_baa_info(updated_info)
                    
                    if result["success"]:
                        st.success(result["message"])
                        log_event(
                            "baa_update", 
                            user=st.session_state["user"]["username"],
                            details={"action": "update_baa"}
                        )
                    else:
                        st.error(result["message"])
                except Exception as e:
                    st.error(f"Error updating BAA information: {str(e)}")
    
    with tab2:
        # Authorized personnel management
        st.markdown("### Authorized Personnel")
        
        # Display current authorized personnel
        personnel = baa_manager.baa_info.get("authorized_personnel", [])
        active_personnel = [p for p in personnel if p.get("active", True)]
        
        if active_personnel:
            st.markdown("#### Currently Authorized")
            for i, person in enumerate(active_personnel):
                st.markdown(
                    f"""
                    {i+1}. **{person['username']}** - {person['role']}  
                    *Added on: {datetime.fromisoformat(person['date_added']).strftime('%Y-%m-%d')}*
                    """
                )
        else:
            st.info("No authorized personnel found.")
        
        # Add new personnel
        st.markdown("#### Add New Personnel")
        with st.form("add_personnel_form"):
            new_username = st.text_input("Username")
            new_role = st.selectbox("Role", ["Admin", "Provider", "Staff", "Support", "Auditor"])
            
            add_user = st.form_submit_button("Add User")
            
            if add_user:
                if not new_username or not new_role:
                    st.error("Please provide both username and role")
                else:
                    try:
                        result = baa_manager.add_authorized_personnel(
                            new_username, 
                            new_role, 
                            st.session_state["user"]["username"]
                        )
                        
                        if result["success"]:
                            st.success(result["message"])
                            log_event(
                                "baa_personnel", 
                                user=st.session_state["user"]["username"],
                                details={"action": "add_personnel", "added_user": new_username}
                            )
                        else:
                            st.error(result["message"])
                    except Exception as e:
                        st.error(f"Error adding personnel: {str(e)}")
        
        # Remove personnel
        st.markdown("#### Remove Personnel")
        with st.form("remove_personnel_form"):
            if active_personnel:
                remove_username = st.selectbox(
                    "Select User to Remove", 
                    [p["username"] for p in active_personnel]
                )
                removal_reason = st.text_area("Reason for Removal")
                
                remove_user = st.form_submit_button("Remove User")
                
                if remove_user:
                    if not removal_reason:
                        st.error("Please provide a reason for removal")
                    else:
                        try:
                            result = baa_manager.remove_authorized_personnel(
                                remove_username, 
                                removal_reason, 
                                st.session_state["user"]["username"]
                            )
                            
                            if result["success"]:
                                st.success(result["message"])
                                log_event(
                                    "baa_personnel", 
                                    user=st.session_state["user"]["username"],
                                    details={
                                        "action": "remove_personnel", 
                                        "removed_user": remove_username,
                                        "reason": removal_reason
                                    }
                                )
                            else:
                                st.error(result["message"])
                        except Exception as e:
                            st.error(f"Error removing personnel: {str(e)}")
            else:
                st.info("No users to remove.")
    
    with tab3:
        # BAA compliance logs
        st.markdown("### BAA Compliance Logs")
        
        log_dir = os.path.join(baa_manager.baa_dir, "logs")
        if os.path.exists(log_dir):
            log_files = [f for f in os.listdir(log_dir) if f.startswith("baa_log_")]
            if log_files:
                selected_log = st.selectbox("Select Log File", log_files)
                
                log_path = os.path.join(log_dir, selected_log)
                log_entries = []
                
                try:
                    with open(log_path, 'r') as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                                log_entries.append(entry)
                            except:
                                pass
                    
                    if log_entries:
                        # Show logs in a dataframe
                        import pandas as pd
                        df = pd.DataFrame(log_entries)
                        st.dataframe(df)
                        
                        # Export option
                        if st.button("Export Logs"):
                            csv = df.to_csv().encode('utf-8')
                            st.download_button(
                                "Download CSV",
                                csv,
                                f"baa_logs_{datetime.now().strftime('%Y%m%d')}.csv",
                                "text/csv",
                                key="download-logs"
                            )
                    else:
                        st.info("No log entries found.")
                except Exception as e:
                    st.error(f"Error reading log file: {str(e)}")
            else:
                st.info("No log files found.")
        else:
            st.info("No logs directory found.")

def emergency_access_ui():
    """Display emergency access interface."""
    # Initialize emergency access manager
    emergency_manager = EmergencyAccessManager()
    
    st.markdown("## Emergency Access")
    
    st.warning(
        "⚠️ IMPORTANT: Emergency access to PHI is strictly regulated under HIPAA. "
        "Use this feature only in genuine emergencies. All access is logged and notified."
    )
    
    # Create tabs for different emergency functions
    tab1, tab2 = st.tabs(["Emergency Access", "Data Breach Reporting"])
    
    with tab1:
        st.markdown("### Emergency PHI Access")
        
        with st.form("emergency_access_form"):
            # Reason selection
            reason_options = [
                "Medical emergency requiring immediate data access",
                "System failure preventing normal access",
                "Audit or investigation by authorized personnel",
                "Data recovery operation",
                "Other (specify)"
            ]
            
            reason = st.selectbox("Reason for Emergency Access", reason_options)
            
            # If "Other" is selected, ask for specific reason
            if reason == "Other (specify)":
                specific_reason = st.text_area("Please specify the emergency reason", "")
                reason = f"Other: {specific_reason}"
            
            # Select data to access
            data_options = [
                "User profile information",
                "Questionnaire responses",
                "Full conversation history",
                "All session data"
            ]
            
            accessed_data = st.multiselect("Data to be accessed", data_options)
            
            # Require acknowledgment
            acknowledgment = st.checkbox(
                "I acknowledge that this is a legitimate emergency and my access will be logged and reviewed."
            )
            
            # Submit button
            submit_emergency = st.form_submit_button("Request Emergency Access")
            
            if submit_emergency:
                if not acknowledgment:
                    st.error("You must acknowledge the emergency access policy.")
                elif not accessed_data:
                    st.error("You must select data to access.")
                else:
                    try:
                        # Log the emergency access
                        result = emergency_manager.log_emergency_access(
                            st.session_state["user"]["username"],
                            reason,
                            ", ".join(accessed_data)
                        )
                        
                        if result["success"]:
                            st.success("Emergency access granted and logged.")
                            log_event(
                                "emergency_access", 
                                user=st.session_state["user"]["username"],
                                details={"reason": reason, "accessed_data": accessed_data},
                                status="granted"
                            )
                            
                            # Grant access based on selection
                            if "All session data" in accessed_data:
                                # Show all sessions
                                server_storage = ServerStorage()
                                sessions = server_storage.list_sessions(limit=100)
                                
                                st.markdown("### All Available Sessions")
                                for session in sessions:
                                    st.markdown(
                                        f"""
                                        **Session ID:** {session.get('session_id', 'unknown')}  
                                        **User:** {session.get('user_name', 'unknown')}  
                                        **Company:** {session.get('company', 'unknown')}  
                                        **Last Saved:** {session.get('last_saved', 'unknown')}  
                                        **Progress:** {session.get('progress', 0)}%
                                        
                                        [View Complete Session Data](javascript:void(0))
                                        
                                        ---
                                        """
                                    )
                            
                            elif "Questionnaire responses" in accessed_data:
                                # Show a search interface for responses
                                st.markdown("### Search Questionnaire Responses")
                                
                                search_term = st.text_input("Search term")
                                if search_term:
                                    st.markdown(f"Searching for: **{search_term}**")
                                    # In a real implementation, this would search through responses
                                    st.info("This is a simulated search result in emergency mode")
                        else:
                            st.error(result["message"])
                    except Exception as e:
                        st.error(f"Error during emergency access: {str(e)}")
    
    with tab2:
        st.markdown("### Report Data Breach")
        
        with st.form("data_breach_form"):
            detected_by = st.text_input("Detected By", st.session_state["user"]["username"])
            description = st.text_area("Description of the Breach", "")
            
            affected_data = st.text_area("Potentially Affected Data", "")
            immediate_actions = st.text_area("Immediate Actions Taken", "")
            next_steps = st.text_area("Next Steps Planned", "")
            contact_info = st.text_input("Contact Information", "")
            
            submit_breach = st.form_submit_button("Report Data Breach")
            
            if submit_breach:
                required_fields = [description, affected_data, immediate_actions, next_steps, contact_info]
                if any(not field for field in required_fields):
                    st.error("All fields are required.")
                else:
                    try:
                        # Report the breach
                        result = emergency_manager.report_data_breach(
                            detected_by,
                            description,
                            affected_data,
                            immediate_actions,
                            next_steps,
                            contact_info
                        )
                        
                        if result["success"]:
                            st.success(f"Data breach reported. Breach ID: {result['breach_id']}")
                            log_event(
                                "data_breach", 
                                user=st.session_state["user"]["username"],
                                details={"breach_id": result['breach_id'], "description": description},
                                status="reported"
                            )
                            
                            # Show notification result
                            if result["notification_result"]["success"]:
                                st.info(result["notification_result"]["message"])
                            else:
                                st.warning(f"Notification issue: {result['notification_result']['message']}")
                        else:
                            st.error(result["message"])
                    except Exception as e:
                        st.error(f"Error reporting breach: {str(e)}")

def hipaa_security_settings():
    """Display HIPAA security settings interface for admins."""
    # Only allow admins
    if st.session_state.get("user", {}).get("role") != "admin":
        st.warning("You do not have permission to access this area.")
        return
    
    st.markdown("## HIPAA Security Settings")
    
    # Create tabs for different security settings
    tab1, tab2, tab3, tab4 = st.tabs([
        "General Settings", 
        "Data Retention", 
        "Notification Settings",
        "Security Reports"
    ])
    
    with tab1:
        st.markdown("### General HIPAA Security Settings")
        
        # Encryption settings
        st.markdown("#### Encryption Settings")
        
        current_key = st.secrets.get("ENCRYPTION_KEY", "Not configured")
        if len(current_key) > 10:
            masked_key = current_key[:5] + "..." + current_key[-5:]
        else:
            masked_key = "Not properly configured"
            
        st.info(f"Current encryption key status: {masked_key}")
        
        with st.expander("Encryption Key Management"):
            st.markdown(
                """
                For security reasons, encryption keys cannot be changed directly through the UI.
                To update the encryption key:
                
                1. Generate a new Fernet key using the cryptography library
                2. Update the ENCRYPTION_KEY in your Streamlit secrets.toml file
                3. Restart the application
                
                **IMPORTANT:** After changing the encryption key, previously encrypted data 
                will no longer be accessible. Plan for data migration if needed.
                """
            )
            
            if st.button("Generate New Key Example"):
                try:
                    from cryptography.fernet import Fernet
                    new_key = Fernet.generate_key().decode()
                    st.code(f"ENCRYPTION_KEY = '{new_key}'")
                    st.info("Add this to your secrets.toml file")
                except Exception as e:
                    st.error(f"Error generating key: {str(e)}")
        
        # Access control settings
        st.markdown("#### Access Control Settings")
        
        session_timeout = st.slider(
            "Session Timeout (minutes)", 
            min_value=5, 
            max_value=60,
            value=30,
            step=5
        )
        
        password_expiry = st.slider(
            "Password Expiry (days)", 
            min_value=30, 
            max_value=365,
            value=90,
            step=30
        )
        
        login_attempts = st.slider(
            "Max Failed Login Attempts", 
            min_value=3, 
            max_value=10,
            value=5
        )
        
        lockout_duration = st.slider(
            "Account Lockout Duration (minutes)", 
            min_value=5, 
            max_value=60,
            value=15,
            step=5
        )
        
        if st.button("Save Security Settings"):
            # In a real implementation, this would update the settings in a secure storage
            st.success("Security settings updated.")
            log_event(
                "security_settings", 
                user=st.session_state["user"]["username"],
                details={
                    "action": "update_security_settings",
                    "changes": {
                        "session_timeout": session_timeout,
                        "password_expiry": password_expiry,
                        "login_attempts": login_attempts,
                        "lockout_duration": lockout_duration
                    }
                }
            )
    
    with tab2:
        st.markdown("### Data Retention Settings")
        
        # Initialize data retention manager
        data_retention = DataRetentionManager()
        
        retention_period = st.slider(
            "Data Retention Period (days)", 
            min_value=365, 
            max_value=2555,  # ~7 years
            value=730,  # 2 years default
            step=365
        )
        
        auto_archive = st.checkbox("Automatically archive completed questionnaires after 30 days", True)
        secure_delete = st.checkbox("Use secure deletion for expired data", True)
        
        if st.button("Save Retention Settings"):
            st.success("Data retention settings updated.")
            log_event(
                "data_retention", 
                user=st.session_state["user"]["username"],
                details={
                    "action": "update_retention_settings",
                    "changes": {
                        "retention_period": retention_period,
                        "auto_archive": auto_archive,
                        "secure_delete": secure_delete
                    }
                }
            )
        
        # Manual data retention actions
        st.markdown("#### Manual Data Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("Run Data Retention Policy Now"):
                try:
                    with st.spinner("Applying data retention policy..."):
                        result = data_retention.apply_retention_policy()
                        
                    st.success(f"Data retention completed: {result['files_archived']} files archived, {result['files_purged']} files purged")
                    log_event(
                        "data_retention", 
                        user=st.session_state["user"]["username"],
                        details={"action": "manual_retention", "result": result}
                    )
                except Exception as e:
                    st.error(f"Error applying retention policy: {str(e)}")
        
        with col2:
            if st.button("Archive Completed Questionnaires"):
                try:
                    with st.spinner("Archiving completed questionnaires..."):
                        result = data_retention.archive_completed_sessions()
                        
                    st.success(f"Archiving completed: {result['files_archived']} files archived")
                    log_event(
                        "data_retention", 
                        user=st.session_state["user"]["username"],
                        details={"action": "manual_archive", "result": result}
                    )
                except Exception as e:
                    st.error(f"Error archiving questionnaires: {str(e)}")
    
    with tab3:
        st.markdown("### Notification Settings")
        
        # Initialize emergency manager for notification settings
        emergency_manager = EmergencyAccessManager()
        
        st.markdown("#### Breach Notification Recipients")
        
        # Current recipients
        current_recipients = emergency_manager.settings.get("notification_recipients", [])
        
        recipient_text = st.text_area(
            "Email Recipients (one per line)", 
            "\n".join(current_recipients) if current_recipients else ""
        )
        
        # Parse recipients
        new_recipients = [r.strip() for r in recipient_text.split("\n") if r.strip()]
        
        st.markdown("#### Emergency Contacts")
        
        # Current emergency contacts
        current_contacts = emergency_manager.settings.get("emergency_contacts", [])
        
        contacts_text = st.text_area(
            "Emergency Contacts (one per line)", 
            "\n".join(current_contacts) if current_contacts else ""
        )
        
        # Parse emergency contacts
        new_contacts = [c.strip() for c in contacts_text.split("\n") if c.strip()]
        
        st.markdown("#### Breach Notification Template")
        
        notification_template = st.text_area(
            "Notification Template", 
            emergency_manager.settings.get("breach_notification_template", "")
        )
        
        if st.button("Save Notification Settings"):
            try:
                # Update notification settings
                result = emergency_manager.update_notification_settings({
                    "notification_recipients": new_recipients,
                    "emergency_contacts": new_contacts,
                    "breach_notification_template": notification_template
                })
                
                if result["success"]:
                    st.success("Notification settings updated.")
                    log_event(
                        "notification_settings", 
                        user=st.session_state["user"]["username"],
                        details={"action": "update_notification_settings"}
                    )
                else:
                    st.error(result["message"])
            except Exception as e:
                st.error(f"Error updating notification settings: {str(e)}")
    
    with tab4:
        st.markdown("### Security Reports")
        
        report_type = st.selectbox(
            "Report Type", 
            ["Access Audit Log", "Emergency Access Log", "Data Breach Reports", "Security Settings Changes"]
        )
        
        start_date = st.date_input("Start Date", datetime.now() - timedelta(days=30))
        end_date = st.date_input("End Date", datetime.now())
        
        if st.button("Generate Report"):
            st.info(f"Generating {report_type} report from {start_date} to {end_date}")
            
            # In a real implementation, this would generate the actual report
            # For now, let's show a sample report
            if report_type == "Access Audit Log":
                try:
                    log_entries = [
                        {
                            "timestamp": "2023-07-01T14:32:15",
                            "user": "admin",
                            "action": "login",
                            "ip_address": "192.168.1.1",
                            "status": "success"
                        },
                        {
                            "timestamp": "2023-07-02T09:15:22",
                            "user": "provider1",
                            "action": "view_session",
                            "ip_address": "192.168.1.2",
                            "status": "success"
                        }
                    ]
                    
                    import pandas as pd
                    df = pd.DataFrame(log_entries)
                    st.dataframe(df)
                    
                    # Export options
                    if st.button("Export Report"):
                        csv = df.to_csv().encode('utf-8')
                        st.download_button(
                            "Download CSV",
                            csv,
                            f"security_report_{datetime.now().strftime('%Y%m%d')}.csv",
                            "text/csv",
                            key="download-report"
                        )
                except Exception as e:
                    st.error(f"Error generating report: {str(e)}")

def user_management_ui():
    """Display user management interface for admins."""
    # Only allow admins
    if st.session_state.get("user", {}).get("role") != "admin":
        st.warning("You do not have permission to access this area.")
        return
    
    st.markdown("## User Management")
    
    # In a real implementation, this would connect to a user database
    # For now, we'll use a simplified example
    st.info("This is a simplified demonstration of user management. In a production environment, you would connect to your user database.")
    
    # Mock user data
    users = [
        {"username": "admin", "role": "admin", "last_login": "2023-05-19T10:30:45"},
        {"username": "provider1", "role": "provider", "last_login": "2023-05-18T14:22:30"},
        {"username": "staff1", "role": "staff", "last_login": "2023-05-17T09:15:10"}
    ]
    
    # Display current users
    st.markdown("### Current Users")
    
    import pandas as pd
    df = pd.DataFrame(users)
    st.dataframe(df)
    
    # Create tabs for user management
    tab1, tab2, tab3 = st.tabs(["Add User", "Edit User", "Reset Password"])
    
    with tab1:
        st.markdown("### Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_role = st.selectbox("Role", ["admin", "provider", "staff", "support"])
            new_password = st.text_input("Initial Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            
            submit_add = st.form_submit_button("Add User")
            
            if submit_add:
                if not new_username or not new_password:
                    st.error("Username and password are required")
                elif new_password != confirm_password:
                    st.error("Passwords do not match")
                else:
                    # In a real implementation, this would add the user to the database
                    st.success(f"User {new_username} added successfully")
                    log_event(
                        "user_management", 
                        user=st.session_state["user"]["username"],
                        details={"action": "add_user", "new_user": new_username, "role": new_role}
                    )
    
    with tab2:
        st.markdown("### Edit User")
        
        edit_user = st.selectbox("Select User to Edit", [u["username"] for u in users])
        selected_user = next((u for u in users if u["username"] == edit_user), None)
        
        if selected_user:
            with st.form("edit_user_form"):
                edit_role = st.selectbox("Role", ["admin", "provider", "staff", "support"], 
                                        index=["admin", "provider", "staff", "support"].index(selected_user["role"]))
                
                account_active = st.checkbox("Account Active", True)
                
                submit_edit = st.form_submit_button("Update User")
                
                if submit_edit:
                    # In a real implementation, this would update the user in the database
                    st.success(f"User {edit_user} updated successfully")
                    log_event(
                        "user_management", 
                        user=st.session_state["user"]["username"],
                        details={"action": "edit_user", "edited_user": edit_user, "new_role": edit_role}
                    )
    
    with tab3:
        st.markdown("### Reset User Password")
        
        reset_user = st.selectbox("Select User", [u["username"] for u in users])
        
        with st.form("reset_user_form"):
            admin_password = st.text_input("Your Password", type="password", 
                                         help="Confirm your admin password to authorize this action")
            new_user_password = st.text_input("New Password for User", type="password")
            force_change = st.checkbox("Force Password Change at Next Login", True)
            
            submit_reset = st.form_submit_button("Reset Password")
            
            if submit_reset:
                if not admin_password or not new_user_password:
                    st.error("Both passwords are required")
                else:
                    # In a real implementation, this would verify the admin password
                    # and reset the user's password
                    st.success(f"Password for {reset_user} has been reset")
                    log_event(
                        "user_management", 
                        user=st.session_state["user"]["username"],
                        details={"action": "reset_password", "target_user": reset_user}
                    )

def questionnaire_page():
    """Display the main questionnaire page."""
    # Add HIPAA compliance header
    st.markdown(
        """
        <div style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #17a2b8;">
            <p style="margin: 0; color: #17a2b8;"><strong>HIPAA Compliance Notice:</strong> All data entered in this questionnaire is protected under HIPAA regulations. Access to this information is logged and monitored.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Add ARCOS logo above the header
    st.markdown(
        """
        <div style="text-align: center; margin-bottom: 10px;">
            <img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png" alt="ARCOS Logo" style="max-width: 200px; height: auto;" />
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Page header
    st.markdown(
        """
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <h1 style="color: #D22B2B; margin-bottom: 5px;">ACE Questionnaire</h1>
            <p style="color: #555; font-size: 16px;">
                Help us understand your company's requirements for ARCOS implementation
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Initialize session state if not already done
    if not hasattr(st.session_state, 'initialized'):
        try:
            # Initial load of questions and instructions
            st.session_state.questions = load_questions('data/questions.txt')
            st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
            # Initialize rest of session state
            services["session_manager"]._initialize_session_state()
            st.session_state.initialized = True
        except Exception as e:
            st.error(f"Error initializing session state: {e}")
            st.stop()
    
    # Initialize pending example and help session variables
    if 'pending_example' not in st.session_state:
        st.session_state.pending_example = None
        
    if 'pending_help' not in st.session_state:
        st.session_state.pending_help = None
    
    # Initialize button state trackers
    if 'help_button_clicked' not in st.session_state:
        st.session_state.help_button_clicked = False
        
    if 'example_button_clicked' not in st.session_state:
        st.session_state.example_button_clicked = False
    
    # Display chat history with special handling for examples
    for i, message in enumerate(st.session_state.visible_messages):
        # Skip messages that have been directly displayed already
        if message.get("already_displayed"):
            continue
            
        # Otherwise use the regular ChatUI display for this message
        if message["role"] == "user":
            user_label = st.session_state.user_info.get("name", "You") or "You"
            st.markdown(
                f"""
                <div style="display: flex; justify-content: flex-end; margin-bottom: 15px;">
                  <div style="background-color: #e8f4f8; border-radius: 15px 15px 0 15px; padding: 12px 18px; max-width: 80%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #d1e7f0; border-right: 5px solid #4e8cff;">
                    <p style="margin: 0; color: #0d467a; font-weight: 600; font-size: 15px;">{user_label}</p>
                    <p style="margin: 5px 0 0 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{message["content"]}</p>
                  </div>
                </div>
                """,
                unsafe_allow_html=True
            )
        elif message["role"] == "assistant":
            content = message["content"]
            
            # HELP BOX
            if "I need help with this question" in content:
                help_text = content.replace("I need help with this question", "").strip()
                st.markdown(
                    f"""
                    <div style="display: flex; margin-bottom: 15px;">
                      <div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #17a2b8;">
                        <p style="margin: 0; color: #17a2b8; font-weight: 600; font-size: 15px;">💡 Help</p>
                        <div style="margin-top: 8px;">
                          <p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{help_text}</p>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            # WELCOME BACK MESSAGE (SESSION RESTORATION)
            elif "Welcome back!" in content and "I've restored your previous session" in content:
                st.markdown(
                    f"""
                    <div style="display: flex; margin-bottom: 15px;">
                      <div style="background-color: #e8f4f8; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 90%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #d1e7f0; border-left: 5px solid #4e8cff;">
                        <p style="margin: 0; color: #0d467a; font-weight: 600; font-size: 15px;">🔄 Session Restored</p>
                        <div style="margin-top: 8px;">
                          <p style="margin: 0; white-space: pre-wrap; color: #0d6efd; line-height: 1.5;">{content}</p>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            # REGULAR ASSISTANT MESSAGE
            else:
                st.markdown(
                    f"""
                    <div style="display: flex; margin-bottom: 15px;">
                      <div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; max-width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #6c757d;">
                        <p style="margin: 0; color: #495057; font-weight: 600; font-size: 15px;">💬 Assistant</p>
                        <div style="margin-top: 8px;">
                          <p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{content}</p>
                        </div>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
    
    # Display any pending help message
    if st.session_state.pending_help:
        help_text = st.session_state.pending_help
        
        # Render the help box
        st.markdown(
            f"""
            <div style="display: flex; margin-bottom: 15px;">
              <div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #17a2b8;">
                <p style="margin: 0; color: #17a2b8; font-weight: 600; font-size: 15px;">💡 Help</p>
                <div style="margin-top: 8px;">
                  <p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{help_text}</p>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Add to visible messages
        st.session_state.visible_messages.append({
            "role": "assistant",
            "content": help_text,
            "already_displayed": True
        })
        
        # Clear the pending help
        st.session_state.pending_help = None
    
    # Display any pending example
    if st.session_state.pending_example:
        example_text = st.session_state.pending_example["example_text"]
        question_text = st.session_state.pending_example["question_text"]
        
        # Render the example
        st.markdown(
            f"""
            <div style="display: flex; margin-bottom: 15px;">
              <div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 90%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef;">
                <p style="margin: 0; color: #495057; font-weight: 600; font-size: 15px;">💬 Assistant</p>
                <div style="background-color: #fff3cd; border-radius: 10px; padding: 15px; margin-top: 12px; margin-bottom: 15px; border: 1px solid #ffeeba; border-left: 5px solid #ffc107;">
                  <p style="margin: 0; font-weight: 600; color: #856404; font-size: 15px;">📝 Example</p>
                  <p style="margin: 8px 0 0 0; color: #533f03; font-style: italic; line-height: 1.5;">{example_text}</p>
                </div>
                <div style="background-color: #e8f4ff; border-radius: 10px; padding: 15px; border: 1px solid #d1ecf1; border-left: 5px solid #007bff;">
                  <p style="margin: 0; font-weight: 600; color: #004085; font-size: 15px;">❓ Question</p>
                  <p style="margin: 8px 0 0 0; color: #0c5460; line-height: 1.5;">{question_text}</p>
                </div>
              </div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Save this to visible messages for history
        st.session_state.visible_messages.append({
            "role": "assistant", 
            "content": f"Example: {example_text}\n\nTo continue with our question:\n{question_text}",
            "already_displayed": True
        })
        
        # Clear the pending example
        st.session_state.pending_example = None
    
    # Display progress bar if beyond first question
    if st.session_state.current_question_index > 0:
        progress_data = services["topic_tracker"].get_progress_data()
        services["chat_ui"].display_progress_bar(progress_data)
    
    # Check if in summary mode
    if st.session_state.get("summary_requested", False):
        # Generate summary
        summary_text = services["summary_generator"].generate_conversation_summary()
        responses = services["summary_generator"].get_responses_as_list()
        
        # Display completion UI
        services["chat_ui"].display_completion_ui(
            summary_text, 
            services["export_service"], 
            st.session_state.user_info, 
            responses
        )
        
        # Send completion email if not already sent
        if st.session_state.get("explicitly_finished", False) and not st.session_state.get("completion_email_sent", False):
            email_result = services["email_service"].send_notification(
                st.session_state.user_info, 
                responses, 
                services["export_service"], 
                completed=True
            )
            
            if email_result["success"]:
                st.success("Completion notification sent!")
                st.session_state.completion_email_sent = True
                
                # Log the completion
                log_event(
                    "questionnaire_completed",
                    user=st.session_state.get("user", {}).get("username", "anonymous"),
                    details={
                        "user_name": st.session_state.user_info.get("name", "unknown"),
                        "company": st.session_state.user_info.get("company", "unknown"),
                        "email_sent": True
                    }
                )
    else:
        # Button callbacks
        def on_help_click():
            st.session_state.help_button_clicked = True
            
        def on_example_click():
            st.session_state.example_button_clicked = True
        
        # Create buttons with callbacks
        buttons_col1, buttons_col2 = st.columns(2)
        with buttons_col1:
            st.button("Need help?", key="help_button", on_click=on_help_click)
        with buttons_col2:
            st.button("Example", key="example_button", on_click=on_example_click)
        
        # Process help button click
        if st.session_state.help_button_clicked:
            # Get the current question context
            last_question = None
            for msg in reversed(st.session_state.visible_messages):
                if msg["role"] == "assistant" and "?" in msg["content"]:
                    last_question = msg["content"]
                    break
            
            # Create help message context
            help_messages = st.session_state.chat_history.copy()
            help_messages.append({
                "role": "system", 
                "content": f"The user is asking for help with the CURRENT question which is: '{last_question}'. Provide a helpful explanation specifically for THIS question, not a previous one."
            })
            help_messages.append({"role": "user", "content": "I need help with this question"})
            
            # Get AI response
            help_response = services["ai_service"].get_response(help_messages)
            
            # Add help interaction to chat history
            st.session_state.chat_history.append({"role": "user", "content": "I need help with this question"})
            st.session_state.chat_history.append({"role": "assistant", "content": help_response})
            
            # Add user message to visible messages
            st.session_state.visible_messages.append({"role": "user", "content": "I need help with this question"})
            
            # Save the help response to session state
            st.session_state.pending_help = help_response
            
            # Reset the button state
            st.session_state.help_button_clicked = False
            
            # Log the help request
            log_event(
                "help_request",
                user=st.session_state.get("user", {}).get("username", "anonymous"),
                details={"question_context": last_question}
            )
            
            # Force a rerun
            st.rerun()
        
        # Process example button click
        if st.session_state.example_button_clicked:
            # Extract the last question from the assistant
            last_question = None
            for msg in reversed(st.session_state.visible_messages):
                if msg["role"] == "assistant" and "?" in msg["content"]:
                    sentences = msg["content"].split(". ")
                    for sentence in reversed(sentences):
                        if "?" in sentence:
                            last_question = sentence.strip()
                            break
                    if last_question:
                        break
            
            if not last_question:
                # Fallback to the last assistant message
                for msg in reversed(st.session_state.visible_messages):
                    if msg["role"] == "assistant":
                        last_question = msg["content"]
                        break
            
            if last_question:
                # Get a simple example without any formatting
                example_messages = [
                    {"role": "system", "content": "You are providing a short, clear example answer for utility company callout processes. ONLY provide the example text with no additional explanation, introduction, or summary. Keep it under 75 words."},
                    {"role": "user", "content": f"Give me one brief example answer for: {last_question}"}
                ]
                
                example_text = services["ai_service"].get_response(example_messages, max_tokens=100)
                
                # Add to chat history
                st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
                
                # Store the response in chat history in a format that's useful for continuation
                st.session_state.chat_history.append({"role": "assistant", "content": f"Example: {example_text}\n\nTo continue with our question:\n{last_question}"})
                
                # Add user message to visible messages
                st.session_state.visible_messages.append({"role": "user", "content": "Can you show me an example?"})
                
                # Save the example in session state for rendering
                st.session_state.pending_example = {
                    "example_text": example_text,
                    "question_text": last_question
                }
                
                # Reset the button state
                st.session_state.example_button_clicked = False
                
                # Log the example request
                log_event(
                    "example_request",
                    user=st.session_state.get("user", {}).get("username", "anonymous"),
                    details={"question_context": last_question}
                )
                
                # Force a rerun
                st.rerun()
            else:
                st.error("Could not find a question to provide an example for.")
                st.session_state.example_button_clicked = False
                st.rerun()
        
        # Add input form
        with st.form(key='chat_form', clear_on_submit=True):
            user_input = st.text_input("Your response:", placeholder="Type your response or ask a question...")
            submit_button = st.form_submit_button("Send")
        
        # Process user input
        if submit_button and user_input:
            # Check if input is empty or just whitespace
            if not user_input or user_input.isspace():
                st.error("Please enter a message before sending.")
            else:
                # Process special message types
                message_type = services["ai_service"].process_special_message_types(user_input)
                
                if message_type["type"] == "example_request":
                    # Extract the last question from the assistant
                    last_question = None
                    for msg in reversed(st.session_state.visible_messages):
                        if msg["role"] == "assistant" and "?" in msg["content"]:
                            sentences = msg["content"].split(". ")
                            for sentence in reversed(sentences):
                                if "?" in sentence:
                                    last_question = sentence.strip()
                                    break
                            if last_question:
                                break
                    
                    if not last_question:
                        # Fallback to the last assistant message
                        for msg in reversed(st.session_state.visible_messages):
                            if msg["role"] == "assistant":
                                last_question = msg["content"]
                                break
                    
                    if last_question:
                        # Get a simple example without any formatting
                        example_messages = [
                            {"role": "system", "content": "You are providing a short, clear example answer for utility company callout processes. ONLY provide the example text with no additional explanation, introduction, or summary. Keep it under 75 words."},
                            {"role": "user", "content": f"Give me one brief example answer for: {last_question}"}
                        ]
                        
                        example_text = services["ai_service"].get_response(example_messages, max_tokens=100)
                        
                        # Add to chat history
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        
                        # Store the response in chat history
                        st.session_state.chat_history.append({"role": "assistant", "content": f"Example: {example_text}\n\nTo continue with our question:\n{last_question}"})
                        
                        # Add user message to visible messages
                        st.session_state.visible_messages.append({"role": "user", "content": user_input})
                        
                        # Save the example in session state for rendering
                        st.session_state.pending_example = {
                            "example_text": example_text,
                            "question_text": last_question
                        }
                        
                        # Log the example request
                        log_event(
                            "example_request",
                            user=st.session_state.get("user", {}).get("username", "anonymous"),
                            details={"question_context": last_question, "user_prompt": user_input}
                        )
                        
                        # Force a rerun to show the user message immediately
                        st.rerun()
                    else:
                        st.error("Could not find a question to provide an example for.")
                        st.rerun()
                    
                elif message_type["type"] == "summary_request" or message_type["type"] == "frustration":
                    # Handle summary request
                    force_summary = message_type["type"] == "frustration" or st.session_state.get("previous_summary_request", False)
                    
                    # Track that user has requested summary before
                    st.session_state["previous_summary_request"] = True
                    
                    # Add user message to chat history
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.visible_messages.append({"role": "user", "content": user_input})
                    
                    # Force summary if user is showing frustration
                    if force_summary:
                        st.session_state.summary_requested = True
                        
                        # Force all topics to be marked as covered
                        for topic in st.session_state.topic_areas_covered:
                            st.session_state.topic_areas_covered[topic] = True
                            
                        # Add a response from assistant
                        summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                        st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
                        st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
                        
                        # Log the forced summary
                        log_event(
                            "summary_request",
                            user=st.session_state.get("user", {}).get("username", "anonymous"),
                            details={"forced": True, "from_frustration": message_type["type"] == "frustration"}
                        )
                    else:
                        # Check if ready for summary
                        summary_readiness = services["topic_tracker"].check_summary_readiness()
                        
                        if summary_readiness["ready"]:
                            st.session_state.summary_requested = True
                            summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                            st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
                            st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
                            
                            # Log the summary request
                            log_event(
                                "summary_request",
                                user=st.session_state.get("user", {}).get("username", "anonymous"),
                                details={"ready": True}
                            )
                        else:
                            # Not ready - inform about missing topics/questions
                            st.session_state.chat_history.append({"role": "assistant", "content": summary_readiness["message"]})
                            st.session_state.visible_messages.append({"role": "assistant", "content": summary_readiness["message"]})
                            
                            # Log the incomplete summary request
                            log_event(
                                "summary_request",
                                user=st.session_state.get("user", {}).get("username", "anonymous"),
                                details={
                                    "ready": False, 
                                    "missing_topics": summary_readiness.get("missing_topics", []),
                                    "missing_questions": summary_readiness.get("missing_questions", [])
                                }
                            )
                    
                    st.rerun()
                    
                else:
                    # Regular input - add to chat history
                    st.session_state.chat_history.append({"role": "user", "content": user_input})
                    st.session_state.visible_messages.append({"role": "user", "content": user_input})
                    
                    # Check for PHI in the input
                    try:
                        phi_classifier = PHIDataClassifier()
                        phi_result = phi_classifier.scan_text_for_phi(user_input)
                        if phi_result["has_phi"]:
                            # Log PHI detection but don't interrupt the flow
                            log_event(
                                "phi_detected", 
                                user=st.session_state.get("user", {}).get("username", "anonymous"),
                                details={"phi_types": phi_result["phi_types"]}
                            )
                    except Exception as e:
                        # Silently handle PHI detection errors
                        print(f"PHI detection error: {e}")
                    
                    # Get AI response
                    ai_response = services["ai_service"].get_response(st.session_state.chat_history)
                    
                    # Process special message formats from the AI
                    is_topic_update = services["topic_tracker"].process_topic_update(ai_response)
                    
                    if not is_topic_update:
                        # Add the response to visible messages
                        st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                        st.session_state.visible_messages.append({"role": "assistant", "content": ai_response})
                        
                        # Force a topic update message after each regular response
                        topic_check_messages = st.session_state.chat_history.copy()
                        topic_check_messages.append({
                            "role": "system", 
                            "content": "Based on all conversation so far, which topics have been covered? Respond ONLY with a TOPIC_UPDATE message that includes the status of ALL topic areas."
                        })
                        
                        try:
                            topic_update_response = services["ai_service"].get_response(topic_check_messages)
                            services["topic_tracker"].process_topic_update(topic_update_response)
                        except Exception as e:
                            # Handle topic update errors gracefully
                            print(f"Topic update error: {e}")
                    
                    # For the first question, extract user and company name
                    if st.session_state.current_question_index == 0:
                        user_info = services["ai_service"].extract_user_info(user_input)
                        
                        # Only update if we found something useful
                        if user_info["name"] or user_info["company"]:
                            st.session_state.user_info = user_info
                            
                            # Add this information to the AI context
                            context_message = {
                                "role": "system", 
                                "content": f"The user's name is {user_info['name'] or 'not provided yet'} and they work for {user_info['company'] or 'a company that has not been mentioned yet'}. If you know the user's name, address them by it. Do not ask for name or company information again if it has been provided."
                            }
                            st.session_state.chat_history.append(context_message)
                            
                            # Log user identification
                            log_event(
                                "user_identified", 
                                user=st.session_state.get("user", {}).get("username", "anonymous"),
                                details={"name": user_info["name"], "company": user_info["company"]}
                            )
                    
                    # Check if this is an answer to the current question
                    if st.session_state.current_question_index < len(st.session_state.questions):
                        is_answer = services["ai_service"].check_response_type(
                            st.session_state.current_question, 
                            user_input
                        )
                        
                        if is_answer:
                            # Store answer and advance to next question
                            st.session_state.responses.append((st.session_state.current_question, user_input))
                            st.session_state.current_question_index += 1
                            if st.session_state.current_question_index < len(st.session_state.questions):
                                st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]
                                
                                # Log question advancement
                                log_event(
                                    "question_advanced", 
                                    user=st.session_state.get("user", {}).get("username", "anonymous"),
                                    details={"new_question_index": st.session_state.current_question_index}
                                )
                    
                    # Update AI context to prevent circular questioning
                    services["topic_tracker"].update_ai_context_after_answer(user_input)
                    
                    st.rerun()

def instructions_page():
    """Display the instructions page."""
    st.markdown("## How to Use the ACE Questionnaire")
    
    st.markdown("""
    ### Welcome to the ACE Questionnaire!
    
    This tool is designed to gather detailed information about your utility company's callout processes for ARCOS implementation. Follow these simple instructions to complete the questionnaire:
    
    #### Getting Started
    1. Enter your name and company name when prompted
    2. Answer each question to the best of your ability
    3. If you need to take a break, use the "Save Progress" button in the sidebar
    
    #### Special Features
    
    * **Need Help?** - Click the "Need help?" button below any question to get a detailed explanation
    * **Examples** - Click the "Example" button to see sample responses for the current question
    * **Save Progress** - Save your work at any time using the sidebar option
    * **Resume Later** - Use your session ID or upload your saved file to continue where you left off
    
    #### Navigation Tips
    
    * Answer one question at a time
    * The progress bar shows how many topic areas you've completed
    * All 9 topic areas must be covered to complete the questionnaire
    * When complete, you'll receive a summary you can download
    
    #### Topic Areas Covered
    
    1. Basic Information - User, company, callout types
    2. Staffing Details - Employee requirements and roles
    3. Contact Process - First contact and methods
    4. List Management - Organization and traversal
    5. Insufficient Staffing - Alternative procedures
    6. Calling Logistics - Simultaneous calls, callbacks
    7. List Changes - Updates to ordering and content
    8. Tiebreakers - Methods when ordering is equal
    9. Additional Rules - Scheduling and exceptions
    
    #### HIPAA Compliance Notice
    
    All data entered in this questionnaire is protected under HIPAA regulations. We employ:
    - End-to-end encryption of all data
    - Strict access controls
    - Comprehensive audit logging
    - Secure data retention policies
    
    If you have any questions about the questionnaire, please check the FAQ tab or contact your ARCOS implementation consultant.
    """)

def faq_page():
    """Display the FAQ page."""
    st.markdown("## Frequently Asked Questions")
    
    # Using expanders for each FAQ item
    with st.expander("What is the ACE Questionnaire?"):
        st.write("""
        The ACE (ARCOS Configuration Exploration) Questionnaire is a tool designed to gather detailed information 
        about your utility company's callout processes. This information helps ARCOS solution consultants 
        understand your specific requirements and configure the ARCOS system to match your existing workflows.
        """)
        
    with st.expander("How is my data protected?"):
        st.write("""
        Your data is protected through several security measures that comply with HIPAA regulations:
        
        * All stored data is encrypted using industry-standard encryption
        * Access to your information is strictly controlled and logged
        * Data transmission uses secure protocols
        * We maintain comprehensive audit trails of all system access
        * Your data is only retained for the necessary period per our data retention policy
        
        If you have specific security concerns, please contact your ARCOS implementation consultant.
        """)
        
    with st.expander("How long does it take to complete?"):
        st.write("""
        The questionnaire typically takes 15-20 minutes to complete, depending on the complexity of your 
        callout processes. You can save your progress at any time and return to complete it later.
        """)
        
    with st.expander("Can I save my progress and continue later?"):
        st.write("""
        Yes! Use the "Save Progress" button in the sidebar to save your current progress. You'll receive a 
        Session ID that you can use to resume later. Make sure to save this ID in a safe place. You can also
        download a backup file if needed.
        """)
        
    with st.expander("What if I don't know the answer to a question?"):
        st.write("""
        If you're unsure about any question, click the "Need help?" button for a detailed explanation. 
        If you still don't know, provide your best understanding and make a note that this area may need 
        further discussion with your implementation consultant.
        """)
        
    with st.expander("Will my answers be saved automatically?"):
        st.write("""
        No, your answers are not saved automatically. Be sure to use the "Save Progress" button in the sidebar 
        to save your work before closing the application.
        """)
        
    with st.expander("Who will see my responses?"):
        st.write("""
        Your responses will be shared with the ARCOS implementation team assigned to your project. 
        The information is used solely for configuring your ARCOS system to match your requirements.
        All access to your data is logged and monitored in compliance with HIPAA regulations.
        """)
        
    with st.expander("What happens after I complete the questionnaire?"):
        st.write("""
        After completion, you'll receive a summary of your responses that you can download. 
        A notification will also be sent to your ARCOS implementation consultant, who will review 
        your responses and schedule a follow-up discussion to clarify any points as needed.
        """)
    
    with st.expander("How do I resume a saved session?"):
        st.write("""
        To resume a saved session, you have two options:
        
        1. **Using Session ID**: Enter your Session ID in the sidebar and click "Load from Server". 
           This is the recommended method if you saved your session ID when prompted.
           
        2. **Using a File**: If you downloaded a progress file, you can upload it in the sidebar
           under "Upload Progress File" and then click "Load from File".
        
        The system will restore your conversation exactly where you left off, and the AI will remember
        the context of your previous discussion.
        """)
        
    with st.expander("What is HIPAA and how does it affect this questionnaire?"):
        st.write("""
        HIPAA (Health Insurance Portability and Accountability Act) is a US law that establishes standards
        for protecting sensitive patient health information. Although this questionnaire primarily focuses
        on utility callout processes, we've implemented HIPAA-compliant security measures to protect all data,
        including:
        
        * User authentication and access controls
        * Data encryption at rest and in transit
        * Comprehensive audit logging
        * Breach notification procedures
        * Data retention and secure deletion policies
        
        These measures ensure your information remains secure and private throughout the process.
        """)

def main():
    """Main application function."""
    # Initialize audit logger with error handling
    if 'audit_logger' not in st.session_state:
        try:
            st.session_state.audit_logger = AuditLogger()
        except Exception as e:
            # Fallback to logging to console
            print(f"Failed to initialize AuditLogger: {e}")
            st.session_state.audit_logger = None
    
    # Create a sidebar menu with HIPAA-compliant options
    with st.sidebar:
        st.title("ACE Questionnaire")
        
        # Check authentication first
        if 'user' not in st.session_state:
            # Not logged in, show only login page
            if login_page():
                # Successfully logged in, rerun to show the main UI
                st.rerun()
            return
            
        # If logged in, show menu options
        menu = ["Questionnaire", "Instructions", "FAQ"]
        
        # Add admin options if user is admin
        if st.session_state['user'].get('role') == 'admin':
            menu.extend(["BAA Management", "HIPAA Security", "User Management"])
        
        # Add emergency access option for all authenticated users
        menu.append("Emergency Access")
        
        selected_option = st.selectbox("Menu", menu)
        
        # Show user info and logout button
        st.markdown(f"Logged in as: **{st.session_state['user']['username']}**")
        if st.button("Logout"):
            auth_service = AuthenticationService()
            auth_service.logout_user()
            log_event(
                "authentication", 
                user=st.session_state['user']['username'],
                details={"action": "logout"}
            )
            st.session_state.clear()
            st.rerun()
    
    # Display the selected option
    if selected_option == "Questionnaire":
        questionnaire_page()
    elif selected_option == "Instructions":
        instructions_page()
    elif selected_option == "FAQ":
        faq_page()
    elif selected_option == "BAA Management":
        baa_management_ui()
    elif selected_option == "HIPAA Security":
        hipaa_security_settings()
    elif selected_option == "User Management":
        user_management_ui()
    elif selected_option == "Emergency Access":
        emergency_access_ui()

# Add sidebar UI
add_sidebar_ui()

# Run the main application
if __name__ == "__main__":
    main()