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

@st.cache_resource
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
    st.markdown("""
    <style>
    body { font-family: sans-serif; }
    .ai-help, .ai-example { background-color: #f8f9fa; padding: 10px; border-radius: 5px; margin: 10px 0; }
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

        if st.button("💾 Save Progress", key="save_progress_button"): # Unique key
            result = services["session_manager"].save_session()
            if result["success"]:
                if result["method"] == "server":
                    st.success(f"Session saved. Your Session ID: {result['session_id']}")
                    st.code(result["session_id"])
                    st.info("Please copy and save this Session ID to resume your progress later.")
                else: # Fallback to file download
                    st.warning(result["message"]) # Inform about fallback
                    st.download_button(
                        label="📥 Download Progress File",
                        data=result["data"],
                        file_name=f"ace_progress_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json",
                        key="download_progress_button" # Unique key
                    )
            else:
                st.error(result["message"])
        
        if st.button("📊 View Progress Dashboard", key="view_progress_button"): # Unique key
            dashboard = services["summary_generator"].generate_progress_dashboard()
            st.session_state.show_dashboard = True
            st.session_state.dashboard_content = dashboard
            st.rerun()

        if st.session_state.get("show_dashboard", False):
            with st.expander("Progress Dashboard", expanded=True):
                st.markdown(st.session_state.dashboard_content)
                st.download_button(
                    label="📥 Download Progress Report",
                    data=st.session_state.dashboard_content,
                    file_name=f"ace_progress_report_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    key="download_report_button" # Unique key
                )
                if st.button("Close Dashboard", key="close_dashboard_button"): # Unique key
                    st.session_state.show_dashboard = False
                    st.rerun()

        st.markdown("---")
        st.markdown("### Resume Progress")
        st.markdown("#### Resume from Server")
        session_id_input = st.text_input("Enter Session ID", key="session_id_input") # Unique key
        if session_id_input and st.button("Load from Server", key="server_load_button"): # Unique key
            result = services["session_manager"].restore_session(source="server", session_id=session_id_input)
            if result["success"]:
                st.success(result["message"])
                st.session_state.app_initialized_first_run = True # Mark as initialized to prevent AI re-greeting
                st.rerun()
            else:
                st.error(result["message"])
        
        st.markdown("#### Or Upload Progress File")
        uploaded_file_data = st.file_uploader("Choose a saved progress file", type=["json"], key="progress_file_uploader") # Unique key
        if uploaded_file_data is not None:
            try:
                content = uploaded_file_data.read().decode("utf-8")
                if st.button("📤 Load from File", key="load_file_button"): # Unique key
                    result = services["session_manager"].restore_session(source="file", file_data=content)
                    if result["success"]:
                        st.success(result["message"])
                        st.session_state.app_initialized_first_run = True # Mark as initialized
                        st.rerun()
                    else:
                        st.error(result["message"])
            except Exception as e:
                st.error(f"Error processing file: {e}")

def main():
    """Main application function."""
    tab1, tab2, tab3 = st.tabs(["Questionnaire", "Instructions", "FAQ"])

    with tab1:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 10px;">
                <img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png" alt="ARCOS Logo" style="max-width: 200px; height: auto;" />
            </div>
            """, unsafe_allow_html=True)
        st.markdown(
            """
            <div style="text-align: center; padding: 10px 0 20px 0;">
                <h1 style="color: #D22B2B; margin-bottom: 5px;">ACE Questionnaire</h1>
                <p style="color: #555; font-size: 16px;">
                    Help us understand your company's requirements for ARCOS implementation
                </p>
            </div>
            """, unsafe_allow_html=True)
        st.warning("""
        **IMPORTANT: Data Privacy Notice**
        Please DO NOT enter any Personal Identifying Information (PII) in this questionnaire...
        This questionnaire is designed to collect information about company processes only.
        """)
        
        # Initialize session state (idempotent)
        # `app_initialized_first_run` controls the initial AI greeting.
        if not hasattr(st.session_state, 'app_initialized_first_run'):
            try:
                # This initializes chat_history with system_prompt, and visible_messages as empty
                services["session_manager"]._initialize_session_state()
                
                # On the very first run for a new session, get the AI's welcome message
                initial_ai_input_messages = st.session_state.chat_history.copy() 
                initial_ai_response = services["ai_service"].get_response(initial_ai_input_messages)

                if initial_ai_response and not initial_ai_response.startswith("Error:") and not initial_ai_response.startswith("Bedrock client not initialized"):
                    st.session_state.chat_history.append({"role": "assistant", "content": initial_ai_response})
                    st.session_state.visible_messages.append({"role": "assistant", "content": initial_ai_response})
                else:
                    st.error(f"Failed to get initial greeting from AI. Details: {initial_ai_response}")
                    st.stop()
                
                st.session_state.app_initialized_first_run = True # Mark that this block has run
                st.rerun() # Rerun to display the initial AI message before asking for user input

            except Exception as e:
                st.error(f"Error during initial application setup: {e}")
                st.stop()
        
        # Ensure other necessary session state variables are present
        if 'pending_example' not in st.session_state: st.session_state.pending_example = None
        if 'pending_help' not in st.session_state: st.session_state.pending_help = None
        if 'help_button_clicked' not in st.session_state: st.session_state.help_button_clicked = False
        if 'example_button_clicked' not in st.session_state: st.session_state.example_button_clicked = False

        # Display chat history
        for message in st.session_state.get("visible_messages", []): # Use .get for safety
            if message["role"] == "user":
                user_label = st.session_state.user_info.get("name", "You") or "You"
                st.markdown(f"""<div style="display: flex; justify-content: flex-end; margin-bottom: 15px;"><div style="background-color: #e8f4f8; border-radius: 15px 15px 0 15px; padding: 12px 18px; max-width: 80%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #d1e7f0; border-right: 5px solid #4e8cff;"><p style="margin: 0; color: #0d467a; font-weight: 600; font-size: 15px;">{user_label}</p><p style="margin: 5px 0 0 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{message["content"]}</p></div></div>""", unsafe_allow_html=True)
            elif message["role"] == "assistant":
                st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; max-width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #6c757d;"><p style="margin: 0; color: #495057; font-weight: 600; font-size: 15px;">💬 Assistant</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{message["content"]}</p></div></div></div>""", unsafe_allow_html=True)

        if st.session_state.pending_help:
            help_text = st.session_state.pending_help
            st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #17a2b8;"><p style="margin: 0; color: #17a2b8; font-weight: 600; font-size: 15px;">💡 Help</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{help_text}</p></div></div></div>""", unsafe_allow_html=True)
            st.session_state.pending_help = None
        
        if st.session_state.pending_example:
            st.markdown(create_example_html(st.session_state.pending_example["example_text"], st.session_state.pending_example["question_text"]), unsafe_allow_html=True)
            st.session_state.pending_example = None
        
        current_question_idx = st.session_state.get("current_question_index", 0)
        if current_question_idx > 0 or (current_question_idx == 0 and len(st.session_state.get("visible_messages", [])) > 1) : # Show progress if beyond the very first AI message
             if not st.session_state.get("summary_requested", False):
                progress_data = services["topic_tracker"].get_progress_data()
                services["chat_ui"].display_progress_bar(progress_data)
        
        if st.session_state.get("summary_requested", False):
            summary_text = services["summary_generator"].generate_conversation_summary()
            responses_list = services["summary_generator"].get_responses_as_list()
            services["chat_ui"].display_completion_ui(summary_text, services["export_service"], st.session_state.user_info, responses_list)
            if st.session_state.get("explicitly_finished", False) and not st.session_state.get("completion_email_sent", False):
                email_result = services["email_service"].send_notification(st.session_state.user_info, responses_list, services["export_service"], completed=True)
                if email_result["success"]:
                    st.success("Completion notification sent!")
                st.session_state.completion_email_sent = True
        else: # Not in summary mode
            def on_help_click(): st.session_state.help_button_clicked = True
            def on_example_click(): st.session_state.example_button_clicked = True
            
            buttons_col1, buttons_col2 = st.columns(2)
            with buttons_col1: st.button("Need help?", key="help_button_main", on_click=on_help_click) # Unique key
            with buttons_col2: st.button("Example", key="example_button_main", on_click=on_example_click) # Unique key
            
            if st.session_state.help_button_clicked:
                st.session_state.help_button_clicked = False # Reset immediately
                last_question_context = st.session_state.current_question
                if st.session_state.visible_messages and st.session_state.visible_messages[-1]["role"] == "assistant":
                     last_question_context = st.session_state.visible_messages[-1]["content"]

                temp_chat_history = st.session_state.chat_history + [{"role": "user", "content": f"I need help with this question: {last_question_context}"}]
                help_response_content = services["ai_service"].get_response(temp_chat_history)
                
                st.session_state.chat_history.append({"role": "user", "content": f"I need help with this question: {last_question_context}"}) # Add actual request to history
                st.session_state.chat_history.append({"role": "assistant", "content": help_response_content})
                st.session_state.visible_messages.append({"role": "user", "content": "I need help with this question."}) # User sees their generic request
                st.session_state.pending_help = help_response_content # Show styled help
                st.rerun()
            
            if st.session_state.example_button_clicked:
                st.session_state.example_button_clicked = False # Reset immediately
                last_question_context = st.session_state.current_question
                if st.session_state.visible_messages and st.session_state.visible_messages[-1]["role"] == "assistant":
                    last_question_content = st.session_state.visible_messages[-1]["content"]
                    # Extract the actual question part if it's a complex assistant message
                    if "To continue with our question:" in last_question_content:
                        last_question_context = last_question_content.split("To continue with our question:")[-1].strip()
                    elif "?" in last_question_content:
                         last_question_context = last_question_content # Assume the whole message is the question context

                if last_question_context:
                    example_text_content = services["ai_service"].get_example_response(last_question_context)
                    full_example_for_history = f"Example: {example_text_content}\n\nTo continue with our question:\n{last_question_context}"
                    
                    st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
                    st.session_state.chat_history.append({"role": "assistant", "content": full_example_for_history})
                    st.session_state.visible_messages.append({"role": "user", "content": "Can you show me an example?"})
                    st.session_state.pending_example = {"example_text": example_text_content, "question_text": last_question_context}
                    st.rerun()
                else:
                    st.error("Could not determine the current question to provide an example for.")

            with st.form(key='chat_form_main_input', clear_on_submit=True): # Unique key
                user_input_val = st.text_input("Your response:", placeholder="Type your response or ask a question...", key="user_response_input") # Unique key
                submit_button_val = st.form_submit_button("Send")
            
            processed_user_input = user_input_val if submit_button_val else None
            
            if processed_user_input:
                if not processed_user_input.strip():
                    st.error("Please enter a message before sending.")
                else:
                    # Add user's original message to visible messages
                    st.session_state.visible_messages.append({"role": "user", "content": processed_user_input})

                    # Prepare guided input for chat history
                    guiding_suffix = (
                        "\n\n[SYSTEM_NOTE_TO_ASSISTANT: Your response to my message above MUST strictly follow the "
                        "MANDATORY TURN STRUCTURE defined in your initial system prompt. This means: "
                        "1. Briefly acknowledge my response if appropriate. "
                        "2. If my response provided substantive information covering a topic, include a TOPIC_UPDATE JSON block on its own line. "
                        "3. CRITICALLY, you MUST then ask the next logical question from the questionnaire guidelines to continue the conversation. "
                        "Do not stop until the questionnaire is complete or a summary is finalized.]"
                    )
                    guided_user_input_for_history = processed_user_input + guiding_suffix
                    st.session_state.chat_history.append({"role": "user", "content": guided_user_input_for_history})
                    
                    # Get AI response using the history with the guided input
                    ai_response_content = services["ai_service"].get_response(st.session_state.chat_history)
                    
                    # Process TOPIC_UPDATE from AI response
                    services["topic_tracker"].process_topic_update(ai_response_content)
                    
                    conversation_part = ai_response_content.split("TOPIC_UPDATE:")[0].strip()
                    if conversation_part: 
                        st.session_state.chat_history.append({"role": "assistant", "content": conversation_part})
                        st.session_state.visible_messages.append({"role": "assistant", "content": conversation_part})
                    elif "TOPIC_UPDATE:" not in ai_response_content and ai_response_content:
                         st.session_state.chat_history.append({"role": "assistant", "content": ai_response_content})
                         st.session_state.visible_messages.append({"role": "assistant", "content": ai_response_content})

                    # Handle user info extraction only on the first substantive user reply
                    # (current_question_index would be 0, and user_info not yet set)
                    current_q_idx_for_user_info = st.session_state.get("current_question_index", 0)
                    is_first_user_reply_after_greeting = len(st.session_state.get("responses", [])) == 0
                    
                    if is_first_user_reply_after_greeting:
                        user_info_data = services["ai_service"].extract_user_info(processed_user_input) # Use original input
                        if user_info_data and (user_info_data.get("name") or user_info_data.get("company")):
                            st.session_state.user_info = user_info_data
                            # Add context to AI about user name/company
                            user_context_system_message = f"User's name is {st.session_state.user_info.get('name', 'not provided')} and company is {st.session_state.user_info.get('company', 'not provided')}. Address them accordingly."
                            st.session_state.chat_history.append({"role": "system", "content": user_context_system_message})


                    # Advance question if current input is an answer
                    questions_list = st.session_state.get("questions", [])
                    if current_q_idx_for_user_info < len(questions_list):
                        is_answer = services["ai_service"].check_response_type(st.session_state.current_question, processed_user_input)
                        if is_answer:
                            st.session_state.responses.append((st.session_state.current_question, processed_user_input))
                            st.session_state.current_question_index += 1
                            if st.session_state.current_question_index < len(questions_list):
                                st.session_state.current_question = questions_list[st.session_state.current_question_index]
                            else: # Questionnaire finished
                                st.session_state.summary_requested = True # Auto-trigger summary
                    
                    services["topic_tracker"].update_ai_context_after_answer(processed_user_input) # Prevent re-asking

                    st.rerun()

    with tab2:
        st.markdown("## How to Use the ACE Questionnaire")
        st.markdown("""...""") # Placeholder for existing Instructions tab content
    
    with tab3:
        st.markdown("## Frequently Asked Questions")
        with st.expander("What is the ACE Questionnaire?"): st.write("...") # Placeholder
        # ... other FAQs

add_sidebar_ui()

if __name__ == "__main__":
    if 'app_initialized_first_run' not in st.session_state:
         # This ensures services are ready and initial AI call logic in main() can proceed
        st.session_state.questions = load_questions('data/questions.txt')
        st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
        # _initialize_session_state will be called inside main if 'app_initialized_first_run' is not set
    main()