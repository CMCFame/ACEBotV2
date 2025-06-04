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
    from modules.topic_tracker import TopicTracker
    from modules.chat_ui import ChatUI
    from modules.summary import SummaryGenerator
    from modules.export import ExportService
    from modules.email_service import EmailService
    from utils.helpers import load_css, apply_css, load_instructions, load_questions
    from config import TOPIC_AREAS
    
    from modules.ai_service import AIService
except ImportError as e:
    st.error(f"Import error: {e}. Please check that all required modules are installed.")
    st.stop()

# Function to create formatted HTML for examples
def create_example_html(example_text, question_text):
    """Create formatted HTML for examples and questions."""
    # ... (existing code for create_example_html)
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
    # ... (existing code for add_sidebar_ui)
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

        if st.button("💾 Save Progress", key="save_progress"):
            result = services["session_manager"].save_session()
            if result["success"]:
                if result["method"] == "server":
                    st.success(f"Session saved. Your Session ID: {result['session_id']}")
                    st.code(result["session_id"])
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
        
        if st.button("📊 View Progress Dashboard", key="view_progress"):
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
                    mime="text/markdown"
                )
                if st.button("Close Dashboard", key="close_dashboard"):
                    st.session_state.show_dashboard = False
                    st.rerun()

        st.markdown("---")
        st.markdown("### Resume Progress")
        st.markdown("#### Resume from Server")
        session_id = st.text_input("Enter Session ID")
        if session_id and st.button("Load from Server", key="server_load"):
            result = services["session_manager"].restore_session(source="server", session_id=session_id)
            if result["success"]:
                st.success(result["message"])
                st.rerun() # Rerun to reflect restored state and trigger AI welcome back
            else:
                st.error(result["message"])
        
        st.markdown("#### Or Upload Progress File")
        uploaded_file = st.file_uploader("Choose a saved progress file", type=["json"], key="progress_file")
        if uploaded_file is not None:
            try:
                content = uploaded_file.read().decode("utf-8")
                if st.button("📤 Load from File", key="load_file"):
                    result = services["session_manager"].restore_session(source="file", file_data=content)
                    if result["success"]:
                        st.success(result["message"])
                        st.rerun() # Rerun to reflect restored state
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
            """,
            unsafe_allow_html=True
        )
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
        st.warning("""
        **IMPORTANT: Data Privacy Notice**
        Please DO NOT enter any Personal Identifying Information (PII) in this questionnaire...
        This questionnaire is designed to collect information about company processes only.
        """)
        
        # Initialize session state if not already done by app.py's first run logic
        if not hasattr(st.session_state, 'app_initialized_first_run'):
            try:
                services["session_manager"]._initialize_session_state() # Initializes chat_history with system_prompt
                st.session_state.app_initialized_first_run = True # Mark that basic init is done

                # <<<< START MODIFICATION >>>>
                # On first run, if no messages are visible, call AI to generate welcome message
                if not st.session_state.visible_messages:
                    # chat_history currently only has the system prompt
                    initial_ai_input_messages = st.session_state.chat_history.copy() 
                    
                    # The AIService.get_response will handle creating a dummy user message
                    # to make Claude respond to the system prompt.
                    initial_ai_response = services["ai_service"].get_response(initial_ai_input_messages)

                    if initial_ai_response and not initial_ai_response.startswith("Error:") and not initial_ai_response.startswith("Bedrock client not initialized"):
                        st.session_state.chat_history.append({"role": "assistant", "content": initial_ai_response})
                        st.session_state.visible_messages.append({"role": "assistant", "content": initial_ai_response})
                        # No st.rerun() here; the rest of the app will render this new message.
                    else:
                        st.error(f"Failed to get initial greeting from AI. Please check Bedrock/Claude configuration. Details: {initial_ai_response}")
                        st.stop() # Stop if AI can't even greet
                # <<<< END MODIFICATION >>>>

            except Exception as e:
                st.error(f"Error initializing session state: {e}")
                st.stop()
        
        # Initialize pending example and help session variables (idempotent)
        if 'pending_example' not in st.session_state: st.session_state.pending_example = None
        if 'pending_help' not in st.session_state: st.session_state.pending_help = None
        if 'help_button_clicked' not in st.session_state: st.session_state.help_button_clicked = False
        if 'example_button_clicked' not in st.session_state: st.session_state.example_button_clicked = False
        
        # Display chat history
        # ... (existing code for displaying chat history, help, examples)
        for i, message in enumerate(st.session_state.visible_messages):
            if message.get("already_displayed"):
                continue
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
                    """, unsafe_allow_html=True)
            elif message["role"] == "assistant":
                content = message["content"]
                if "I need help with this question" in content:
                    help_text = content.replace("I need help with this question", "").strip()
                    st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #17a2b8;"><p style="margin: 0; color: #17a2b8; font-weight: 600; font-size: 15px;">💡 Help</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{help_text}</p></div></div></div>""", unsafe_allow_html=True)
                elif "Welcome back!" in content and "I've restored your previous session" in content:
                    st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #e8f4f8; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 90%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #d1e7f0; border-left: 5px solid #4e8cff;"><p style="margin: 0; color: #0d467a; font-weight: 600; font-size: 15px;">🔄 Session Restored</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #0d6efd; line-height: 1.5;">{content}</p></div></div></div>""", unsafe_allow_html=True)
                else: # Regular assistant or example/question combo
                    # Check if it's an example/question combo that should use create_example_html
                    # This relies on pending_example being cleared *after* display
                    # The new display logic for pending example/help is better.
                    st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; max-width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #6c757d;"><p style="margin: 0; color: #495057; font-weight: 600; font-size: 15px;">💬 Assistant</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{content}</p></div></div></div>""", unsafe_allow_html=True)


        if st.session_state.pending_help:
            help_text = st.session_state.pending_help
            st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #17a2b8;"><p style="margin: 0; color: #17a2b8; font-weight: 600; font-size: 15px;">💡 Help</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{help_text}</p></div></div></div>""", unsafe_allow_html=True)
            if not any(msg["role"] == "assistant" and msg["content"] == help_text for msg in st.session_state.visible_messages):
                st.session_state.visible_messages.append({"role": "assistant", "content": help_text, "already_displayed": True}) # Mark as displayed
            st.session_state.pending_help = None
        
        if st.session_state.pending_example:
            example_text = st.session_state.pending_example["example_text"]
            question_text = st.session_state.pending_example["question_text"]
            st.markdown(create_example_html(example_text, question_text), unsafe_allow_html=True)
            full_example_content = f"Example: {example_text}\n\nTo continue with our question:\n{question_text}"
            if not any(msg["role"] == "assistant" and msg["content"] == full_example_content for msg in st.session_state.visible_messages):
                 st.session_state.visible_messages.append({"role": "assistant", "content": full_example_content, "already_displayed": True}) # Mark as displayed
            st.session_state.pending_example = None

        if st.session_state.current_question_index > 0 : # Show progress if not on the very first AI-generated question
             if not st.session_state.get("summary_requested", False): # And not in summary mode
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
        else:
            def on_help_click(): st.session_state.help_button_clicked = True
            def on_example_click(): st.session_state.example_button_clicked = True
            
            buttons_col1, buttons_col2 = st.columns(2)
            with buttons_col1: st.button("Need help?", key="help_button", on_click=on_help_click)
            with buttons_col2: st.button("Example", key="example_button", on_click=on_example_click)
            
            if st.session_state.help_button_clicked:
                last_question = None
                for msg in reversed(st.session_state.visible_messages): # Check visible messages for last question context
                    if msg["role"] == "assistant" and "?" in msg["content"]:
                        last_question = msg["content"].split("To continue with our question:")[-1].strip() if "To continue with our question:" in msg["content"] else msg["content"]
                        break
                if not last_question: last_question = st.session_state.current_question # Fallback
                
                help_messages_for_ai = st.session_state.chat_history.copy()
                help_messages_for_ai.append({"role": "user", "content": f"I need help with this question: {last_question}"})
                help_response_content = services["ai_service"].get_response(help_messages_for_ai)
                
                st.session_state.chat_history.append({"role": "user", "content": f"I need help with this question: {last_question}"})
                st.session_state.chat_history.append({"role": "assistant", "content": help_response_content})
                # Do not add to visible_messages here, pending_help will handle it
                st.session_state.pending_help = help_response_content
                st.session_state.help_button_clicked = False
                st.rerun()
            
            if st.session_state.example_button_clicked:
                last_question = None
                for msg in reversed(st.session_state.visible_messages): # Check visible messages
                    if msg["role"] == "assistant" and "?" in msg["content"]:
                        content_parts = msg["content"].split("To continue with our question:")
                        last_question = content_parts[-1].strip() if len(content_parts) > 1 else msg["content"].strip()
                        break
                if not last_question: last_question = st.session_state.current_question # Fallback

                if last_question:
                    example_text_content = services["ai_service"].get_example_response(last_question) # This is just the example part
                    full_example_for_history = f"Example: {example_text_content}\n\nTo continue with our question:\n{last_question}"
                    
                    st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
                    st.session_state.chat_history.append({"role": "assistant", "content": full_example_for_history})
                    # Do not add to visible_messages here, pending_example will handle it
                    st.session_state.pending_example = {"example_text": example_text_content, "question_text": last_question}
                    st.session_state.example_button_clicked = False
                    st.rerun()
                else:
                    st.error("Could not find a question to provide an example for.")
                    st.session_state.example_button_clicked = False

            with st.form(key='chat_form_main', clear_on_submit=True):
                user_input = st.text_input("Your response:", placeholder="Type your response or ask a question...")
                submit_button = st.form_submit_button("Send")
            
            processed_input = user_input if submit_button else None
            
            if processed_input:
                if not processed_input.strip():
                    st.error("Please enter a message before sending.")
                else:
                    message_type = services["ai_service"].process_special_message_types(processed_input)
                    
                    if message_type["type"] == "example_request":
                        st.session_state.example_button_clicked = True # Trigger example logic
                        st.rerun()
                    elif message_type["type"] == "summary_request" or message_type["type"] == "frustration":
                        st.session_state.chat_history.append({"role": "user", "content": processed_input})
                        st.session_state.visible_messages.append({"role": "user", "content": processed_input})
                        force_summary = message_type["type"] == "frustration" or st.session_state.get("previous_summary_request", False)
                        st.session_state["previous_summary_request"] = True
                        
                        if force_summary:
                            st.session_state.summary_requested = True
                            for topic in st.session_state.topic_areas_covered: st.session_state.topic_areas_covered[topic] = True
                            summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                        else:
                            summary_readiness = services["topic_tracker"].check_summary_readiness()
                            if summary_readiness["ready"]:
                                st.session_state.summary_requested = True
                                summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                            else:
                                summary_confirm = summary_readiness["message"]
                        
                        st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
                        st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
                        st.rerun()
                    else: # Regular input
                        st.session_state.chat_history.append({"role": "user", "content": processed_input})
                        st.session_state.visible_messages.append({"role": "user", "content": processed_input})
                        
                        ai_response_content = services["ai_service"].get_response(st.session_state.chat_history)
                        
                        services["topic_tracker"].process_topic_update(ai_response_content) # Process hidden TOPIC_UPDATE
                        
                        conversation_part = ai_response_content.split("TOPIC_UPDATE:")[0].strip()
                        if conversation_part: # Only add if there's actual conversation content
                            st.session_state.chat_history.append({"role": "assistant", "content": conversation_part})
                            st.session_state.visible_messages.append({"role": "assistant", "content": conversation_part})
                        elif "TOPIC_UPDATE:" not in ai_response_content : # No topic update, full message is conversation
                             st.session_state.chat_history.append({"role": "assistant", "content": ai_response_content})
                             st.session_state.visible_messages.append({"role": "assistant", "content": ai_response_content})


                        if st.session_state.current_question_index == 0 and not st.session_state.user_info.get("name"): # Only extract if not already done
                            user_info_data = services["ai_service"].extract_user_info(processed_input)
                            if user_info_data["name"] or user_info_data["company"]:
                                st.session_state.user_info = user_info_data

                        if st.session_state.current_question_index < len(st.session_state.questions):
                            is_answer = services["ai_service"].check_response_type(st.session_state.current_question, processed_input)
                            if is_answer:
                                st.session_state.responses.append((st.session_state.current_question, processed_input))
                                st.session_state.current_question_index += 1
                                if st.session_state.current_question_index < len(st.session_state.questions):
                                    st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]
                        st.rerun()

    with tab2:
        # ... (existing Instructions tab content)
        st.markdown("## How to Use the ACE Questionnaire")
        st.markdown("""...""") # Keep existing content
    
    with tab3:
        # ... (existing FAQ tab content)
        st.markdown("## Frequently Asked Questions")
        with st.expander("What is the ACE Questionnaire?"): st.write("...")
        # Keep existing expanders

add_sidebar_ui()

if __name__ == "__main__":
    main()