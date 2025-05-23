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
from datetime import datetime

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
                else:
                    st.warning(result["message"])
                    st.download_button(
                        label="📥 Download Progress File",
                        data=result["data"],
                        file_name=f"ace_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_progress"
                    )
            else:
                st.error(result["message"])
        
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
                st.rerun()
            else:
                st.error(result["message"])
        
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
                        st.rerun()
                    else:
                        st.error(result["message"])
            except Exception as e:
                st.error(f"Error processing file: {e}")

def main():
    """Main application function."""
    # Create tabs
    tab1, tab2, tab3 = st.tabs(["Questionnaire", "Instructions", "FAQ"])

    with tab1:
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
        
        # Add PII Disclosure banner
        st.warning("""
        **IMPORTANT: Data Privacy Notice**
        
        Please DO NOT enter any Personal Identifying Information (PII) in this questionnaire, including:
        
        • Home addresses or personal contact information
        • Social security numbers or government IDs
        • Personal financial information
        • Any other sensitive personal data
        
        This questionnaire is designed to collect information about company processes only.
        """)
        
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
                "content": help_text
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
                "content": f"Example: {example_text}\n\nTo continue with our question:\n{question_text}"
            })
            
            # Clear the pending example so it doesn't show again
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
        else:
            # Add help/example buttons if not in summary mode - REPLACED with callback versions
            # help_button, example_button = services["chat_ui"].add_help_example_buttons()
            
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
            
            # Process help button click - UPDATED to use session state
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
                
                # Force a rerun
                st.rerun()
            
            # Process example button click - UPDATED to use session state
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
                    
                    # Force a rerun
                    st.rerun()
                else:
                    st.error("Could not find a question to provide an example for.")
                    st.session_state.example_button_clicked = False
                    st.rerun()
            
            # Add input form
            user_input = services["chat_ui"].add_input_form()
            
            # Process user input
            if user_input:
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
                        else:
                            # Check if ready for summary
                            summary_readiness = services["topic_tracker"].check_summary_readiness()
                            
                            if summary_readiness["ready"]:
                                st.session_state.summary_requested = True
                                summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                                st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
                                st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
                            else:
                                # Not ready - inform about missing topics/questions
                                st.session_state.chat_history.append({"role": "assistant", "content": summary_readiness["message"]})
                                st.session_state.visible
                                st.session_state.chat_history.append({"role": "assistant", "content": summary_readiness["message"]})
                                st.session_state.visible_messages.append({"role": "assistant", "content": summary_readiness["message"]})
                        
                        st.rerun()
                        
                    else:
                        # Regular input - add to chat history
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.visible_messages.append({"role": "user", "content": user_input})
                        
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
                            
                            topic_update_response = services["ai_service"].get_response(topic_check_messages)
                            services["topic_tracker"].process_topic_update(topic_update_response)
                        
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
                        
                        # Update AI context to prevent circular questioning
                        services["topic_tracker"].update_ai_context_after_answer(user_input)
                        
                        st.rerun()

    with tab2:
        # Instructions Tab Content
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
        
        If you have any questions about the questionnaire, please check the FAQ tab or contact your ARCOS implementation consultant.
        """)
    
    with tab3:
        # FAQ Tab Content
        st.markdown("## Frequently Asked Questions")
        
        # Using expanders for each FAQ item
        with st.expander("What is the ACE Questionnaire?"):
            st.write("""
            The ACE (ARCOS Configuration Exploration) Questionnaire is a tool designed to gather detailed information 
            about your utility company's callout processes. This information helps ARCOS solution consultants 
            understand your specific requirements and configure the ARCOS system to match your existing workflows.
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

# Add sidebar UI
add_sidebar_ui()

# Run the main application
if __name__ == "__main__":
    main()