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
import re # Import regex module
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
    st.error(f"Import error: {e}. Please check that all required modules are installed and paths are correct.")
    st.stop()

# Function to create formatted HTML for examples
def create_example_html(example_text, question_text):
    """Create formatted HTML for examples and questions."""
    # This function is primarily for displaying examples requested by the user.
    # It formats the assistant's output when it includes an example and re-asks the question.
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
    ai_service = AIService() # Ensure AIService() doesn't require API key here if handled by secrets/env
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
    /* Add other minimal essential styles if needed */
    </style>
    """, unsafe_allow_html=True)

def add_sidebar_ui():
    """Add the sidebar UI elements."""
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png"
                     alt="ARCOS Logo" style="max-width: 80%; height: auto; margin: 10px auto;" />
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

        if st.button("💾 Save Progress", key="save_progress_button"):
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
                        key="download_progress_button"
                    )
            else:
                st.error(result["message"])
        
        if st.button("📊 View Progress Dashboard", key="view_progress_button"): 
            # Ensure summary_generator can access session state for dashboard data
            dashboard_content = services["summary_generator"].generate_progress_dashboard()
            st.session_state.show_dashboard = True
            st.session_state.dashboard_content = dashboard_content # Store for display
            st.rerun()

        if st.session_state.get("show_dashboard", False):
            with st.expander("Progress Dashboard", expanded=True):
                st.markdown(st.session_state.get("dashboard_content", "Could not load dashboard content."))
                st.download_button(
                    label="📥 Download Progress Report",
                    data=st.session_state.get("dashboard_content", ""),
                    file_name=f"ace_progress_report_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown",
                    key="download_report_button"
                )
                if st.button("Close Dashboard", key="close_dashboard_button"): 
                    st.session_state.show_dashboard = False
                    st.rerun()

        st.markdown("---")
        st.markdown("### Resume Progress")
        st.markdown("#### Resume from Server")
        session_id_input = st.text_input("Enter Session ID", key="session_id_input_key") 
        if session_id_input and st.button("Load from Server", key="server_load_button"): 
            result = services["session_manager"].restore_session(source="server", session_id=session_id_input)
            if result["success"]:
                st.success(result["message"])
                st.session_state.app_initialized_first_run = True # Important: Mark as initialized
                st.rerun()
            else:
                st.error(result["message"])
        
        st.markdown("#### Or Upload Progress File")
        uploaded_file_data = st.file_uploader("Choose a saved progress file", type=["json"], key="progress_file_uploader")
        if uploaded_file_data is not None:
            try:
                content = uploaded_file_data.read().decode("utf-8")
                if st.button("📤 Load from File", key="load_file_button"): 
                    result = services["session_manager"].restore_session(source="file", file_data=content)
                    if result["success"]:
                        st.success(result["message"])
                        st.session_state.app_initialized_first_run = True # Important: Mark as initialized
                        st.rerun()
                    else:
                        st.error(result["message"])
            except Exception as e:
                st.error(f"Error processing file: {e}")

def main():
    """Main application function."""
    tab1, tab2, tab3 = st.tabs(["Questionnaire", "Instructions", "FAQ"])

    with tab1:
        # Header, Logo, PII Warning (keep as is)
        st.markdown("""<div style="text-align: center; margin-bottom: 10px;"><img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png" alt="ARCOS Logo" style="max-width: 200px; height: auto;" /></div>""", unsafe_allow_html=True)
        st.markdown("""<div style="text-align: center; padding: 10px 0 20px 0;"><h1 style="color: #D22B2B; margin-bottom: 5px;">ACE Questionnaire</h1><p style="color: #555; font-size: 16px;">Help us understand your company's requirements for ARCOS implementation</p></div>""", unsafe_allow_html=True)
        st.warning("""**IMPORTANT: Data Privacy Notice** Please DO NOT enter any Personal Identifying Information (PII)...""")
        
        # Initialize session state ONCE per session for the very first run
        if not st.session_state.get('app_initialized_first_run', False):
            try:
                # This initializes chat_history with system_prompt, and visible_messages as empty
                services["session_manager"]._initialize_session_state() 
                
                # On first run, get the AI's welcome message
                initial_ai_input_messages = st.session_state.chat_history.copy() 
                initial_ai_response = services["ai_service"].get_response(initial_ai_input_messages)

                if initial_ai_response and not initial_ai_response.startswith("Error:") and not initial_ai_response.startswith("Bedrock client not initialized"):
                    # The initial response should not contain TOPIC_UPDATE, but clean it just in case
                    topic_update_pattern = r"TOPIC_UPDATE:\s*\{.*?\}"
                    cleaned_initial_response = re.sub(topic_update_pattern, "", initial_ai_response, flags=re.DOTALL).strip()
                    cleaned_initial_response = "\n".join([line for line in cleaned_initial_response.splitlines() if line.strip()])

                    if cleaned_initial_response:
                        st.session_state.chat_history.append({"role": "assistant", "content": cleaned_initial_response}) # Store cleaned
                        st.session_state.visible_messages.append({"role": "assistant", "content": cleaned_initial_response})
                else:
                    st.error(f"Failed to get initial greeting from AI. Details: {initial_ai_response}")
                    st.stop() 
                
                st.session_state.app_initialized_first_run = True # Mark that this block has run
                st.rerun() # Rerun to display the initial AI message

            except Exception as e:
                st.error(f"Error during initial application setup: {e}")
                st.stop()
        
        # Ensure other necessary session state variables are present
        if 'pending_example' not in st.session_state: st.session_state.pending_example = None
        if 'pending_help' not in st.session_state: st.session_state.pending_help = None
        if 'help_button_clicked' not in st.session_state: st.session_state.help_button_clicked = False
        if 'example_button_clicked' not in st.session_state: st.session_state.example_button_clicked = False

        # Display chat history (using ChatUI's method is an option, or direct markdown)
        for message in st.session_state.get("visible_messages", []):
            role = message.get("role")
            content = message.get("content","")
            if role == "user":
                user_label = st.session_state.user_info.get("name", "You") or "You"
                st.markdown(f"""<div style="display: flex; justify-content: flex-end; margin-bottom: 15px;"><div style="background-color: #e8f4f8; border-radius: 15px 15px 0 15px; padding: 12px 18px; max-width: 80%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #d1e7f0; border-right: 5px solid #4e8cff;"><p style="margin: 0; color: #0d467a; font-weight: 600; font-size: 15px;">{user_label}</p><p style="margin: 5px 0 0 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{content}</p></div></div>""", unsafe_allow_html=True)
            elif role == "assistant": # Handles regular + help/example structure
                st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; max-width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #6c757d;"><p style="margin: 0; color: #495057; font-weight: 600; font-size: 15px;">💬 Assistant</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{content}</p></div></div></div>""", unsafe_allow_html=True)
        
        # Display pending help or example (these are now rendered as part of visible_messages directly)
        # The logic for pending_help/example now primarily sets up the AI call and adds to visible_messages.

        current_q_idx = st.session_state.get("current_question_index", 0)
        # Show progress if beyond the very first AI message AND not in summary mode
        if (current_q_idx > 0 or (current_q_idx == 0 and len(st.session_state.get("visible_messages", [])) > 1)) and \
           not st.session_state.get("summary_requested", False):
            progress_data = services["topic_tracker"].get_progress_data()
            services["chat_ui"].display_progress_bar(progress_data) # Assumes chat_ui has this method
        
        if st.session_state.get("summary_requested", False):
            summary_text = services["summary_generator"].generate_conversation_summary()
            responses_list = services["summary_generator"].get_responses_as_list() # For export
            services["chat_ui"].display_completion_ui(summary_text, services["export_service"], st.session_state.user_info, responses_list)
            if st.session_state.get("explicitly_finished", False) and not st.session_state.get("completion_email_sent", False):
                email_result = services["email_service"].send_notification(st.session_state.user_info, responses_list, services["export_service"], completed=True)
                if email_result["success"]: st.success("Completion notification sent!")
                st.session_state.completion_email_sent = True
        else: # Not in summary mode - active chat
            def on_help_click(): st.session_state.help_button_clicked = True
            def on_example_click(): st.session_state.example_button_clicked = True
            
            buttons_col1, buttons_col2 = st.columns(2)
            with buttons_col1: st.button("Need help?", key="help_button_main_chat", on_click=on_help_click)
            with buttons_col2: st.button("Example", key="example_button_main_chat", on_click=on_example_click)
            
            if st.session_state.help_button_clicked:
                st.session_state.help_button_clicked = False 
                last_question_context = st.session_state.get("current_question", "the current topic")
                # Try to get a more specific question from the last assistant message if available
                if st.session_state.visible_messages and st.session_state.visible_messages[-1]["role"] == "assistant":
                     assistant_last_msg = st.session_state.visible_messages[-1]["content"]
                     if "?" in assistant_last_msg: last_question_context = assistant_last_msg

                temp_chat_history = st.session_state.chat_history + [{"role": "user", "content": f"I need help with this question: {last_question_context}"}]
                help_response_content = services["ai_service"].get_response(temp_chat_history)
                
                st.session_state.visible_messages.append({"role": "user", "content": "I need help with this question."}) # User sees generic request
                st.session_state.visible_messages.append({"role": "assistant", "content": help_response_content}) # Display AI's help
                st.session_state.chat_history.append({"role": "user", "content": f"I need help with this question: {last_question_context}"}) # Add specific request to history
                st.session_state.chat_history.append({"role": "assistant", "content": help_response_content}) # Add AI help to history
                st.rerun()
            
            if st.session_state.example_button_clicked:
                st.session_state.example_button_clicked = False
                last_question_context = st.session_state.get("current_question", "the current topic")
                if st.session_state.visible_messages and st.session_state.visible_messages[-1]["role"] == "assistant":
                    assistant_last_msg_content = st.session_state.visible_messages[-1]["content"]
                    # Extract the question part if "To continue..." is present
                    if "To continue with our question:" in assistant_last_msg_content:
                        last_question_context = assistant_last_msg_content.split("To continue with our question:")[-1].strip()
                    elif "?" in assistant_last_msg_content: # Otherwise, use the whole message if it's a question
                        last_question_context = assistant_last_msg_content
                
                if last_question_context:
                    example_text_content = services["ai_service"].get_example_response(last_question_context)
                    # This response should be just the example, AI service handles formatting if needed
                    
                    # Format for display using create_example_html
                    formatted_example_display = create_example_html(example_text_content, last_question_context)
                    
                    st.session_state.visible_messages.append({"role": "user", "content": "Can you show me an example?"})
                    st.session_state.visible_messages.append({"role": "assistant", "content": formatted_example_display}) # Show formatted
                    
                    # Add to chat history in a way AI understands for context
                    history_example_text = f"Example: {example_text_content}\n\nTo continue with our question:\n{last_question_context}"
                    st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
                    st.session_state.chat_history.append({"role": "assistant", "content": history_example_text})
                    st.rerun()
                else:
                    st.error("Could not determine the current question to provide an example for.")

            with st.form(key='chat_form_main_input_key', clear_on_submit=True):
                user_input_val = st.text_input("Your response:", placeholder="Type your response or ask a question...", key="user_response_input_key")
                submit_button_val = st.form_submit_button("Send")
            
            processed_user_input = user_input_val if submit_button_val else None
            
            if processed_user_input:
                if not processed_user_input.strip():
                    st.error("Please enter a message before sending.")
                else:
                    st.session_state.visible_messages.append({"role": "user", "content": processed_user_input})
                    guiding_suffix = (
                        "\n\n[SYSTEM_NOTE_TO_ASSISTANT: Your response to my message above MUST strictly follow the "
                        "MANDATORY TURN STRUCTURE defined in your initial system prompt. This means: "
                        "1. Briefly acknowledge my response if appropriate. "
                        "2. If my response provided substantive information covering a topic, include a TOPIC_UPDATE JSON block on its own line if appropriate. "
                        "3. CRITICALLY, you MUST then ask the next logical question from the questionnaire guidelines to continue the conversation. "
                        "Do not stop until the questionnaire is complete or a summary is finalized.]"
                    )
                    guided_user_input_for_history = processed_user_input + guiding_suffix
                    st.session_state.chat_history.append({"role": "user", "content": guided_user_input_for_history})
                    
                    raw_ai_response_content = services["ai_service"].get_response(st.session_state.chat_history)
                    
                    if "SUMMARY_REQUEST" in raw_ai_response_content:
                        st.session_state.summary_requested = True
                        conversation_part_before_summary = raw_ai_response_content.split("SUMMARY_REQUEST")[0].strip()
                        if conversation_part_before_summary:
                            st.session_state.chat_history.append({"role": "assistant", "content": conversation_part_before_summary})
                            st.session_state.visible_messages.append({"role": "assistant", "content": conversation_part_before_summary})
                        st.session_state.chat_history.append({"role": "system", "content": "[SYSTEM_NOTE] Summary has been requested. Do not ask further questions."})
                        st.rerun()
                    else:
                        services["topic_tracker"].process_topic_update(raw_ai_response_content) 
                        
                        topic_update_pattern = r"TOPIC_UPDATE:\s*\{.*?\}" 
                        display_content = re.sub(topic_update_pattern, "", raw_ai_response_content, flags=re.DOTALL).strip() 
                        display_content = "\n".join([line for line in display_content.splitlines() if line.strip()])

                        if display_content: 
                            st.session_state.chat_history.append({"role": "assistant", "content": display_content})
                            st.session_state.visible_messages.append({"role": "assistant", "content": display_content})
                        
                        question_asked_in_display_content = "?" in display_content
                        
                        if not question_asked_in_display_content and not st.session_state.get("summary_requested", False):
                            force_question_history = st.session_state.chat_history.copy()
                            # If display_content (the first part of AI's response) wasn't added because it was empty after stripping TOPIC_UPDATE,
                            # we should ensure the last assistant message in force_question_history is the raw_ai_response_content (or its conversational part)
                            # so the AI has context for "your previous response".
                            # This is complex; simpler is to ensure AI knows it needs to ask a new question.
                            
                            force_question_instruction = (
                                "[SYSTEM_TASK] Your previous response did not end with a question. "
                                "Review the entire conversation history, your main system prompt (especially 'Required Information Checklist' and 'MANDATORY TURN STRUCTURE'), "
                                "and current topic coverage. Determine and ask the single most relevant next question to continue the questionnaire. "
                                "Respond ONLY with that question. No apologies or other conversational text."
                            )
                            force_question_history.append({"role": "system", "content": force_question_instruction})
                            next_question_response = services["ai_service"].get_response(force_question_history, max_tokens=200) # Increased tokens slightly for clarity
                            
                            if next_question_response and not next_question_response.startswith("Error:"):
                                # This will be a new assistant message
                                st.session_state.chat_history.append({"role": "assistant", "content": next_question_response})
                                st.session_state.visible_messages.append({"role": "assistant", "content": next_question_response})
                            else:
                                st.error(f"Assistant failed to provide a follow-up question. Response: {next_question_response}")
                    
                    # User info extraction & Question advancement
                    current_q_idx = st.session_state.get("current_question_index", 0)
                    questions_list = st.session_state.get("questions", [])
                    
                    # Only extract user info if it's not already captured and it's the first real interaction
                    if len(st.session_state.get("responses", [])) == 0 and not (st.session_state.user_info.get("name") or st.session_state.user_info.get("company")):
                        user_info_data = services["ai_service"].extract_user_info(processed_user_input)
                        if user_info_data and (user_info_data.get("name") or user_info_data.get("company")):
                            st.session_state.user_info = user_info_data
                            user_context_msg = f"System note: User is {user_info_data.get('name', 'N/A')} from {user_info_data.get('company', 'N/A')}."
                            if not any(m.get("content") == user_context_msg for m in st.session_state.chat_history if m.get("role")=="system"):
                                st.session_state.chat_history.append({"role": "system", "content": user_context_msg})
                    
                    current_official_question_text = st.session_state.get("current_question", questions_list[0] if questions_list else "")
                    if current_q_idx < len(questions_list) and current_official_question_text:
                        # Use the last AI message shown to user as context for check_response_type
                        last_ai_msg_for_check = ""
                        if st.session_state.visible_messages and st.session_state.visible_messages[-1]['role'] == 'assistant':
                            last_ai_msg_for_check = st.session_state.visible_messages[-1]['content']
                        
                        # If the last AI message was just a forced question, it's more direct
                        # Otherwise, it might be a longer conversational turn.
                        is_answer = services["ai_service"].check_response_type(last_ai_msg_for_check or current_official_question_text, processed_user_input)
                        
                        if is_answer:
                            st.session_state.responses.append((current_official_question_text, processed_user_input))
                            st.session_state.current_question_index += 1
                            if st.session_state.current_question_index < len(questions_list):
                                st.session_state.current_question = questions_list[st.session_state.current_question_index]
                            else: 
                                st.session_state.summary_requested = True # End of official questions list
                    
                    services["topic_tracker"].update_ai_context_after_answer(processed_user_input)
                    st.rerun()

    with tab2:
        st.markdown("## How to Use the ACE Questionnaire")
        st.markdown(""" ... (Your existing detailed instructions) ... """)
    
    with tab3:
        st.markdown("## Frequently Asked Questions")
        # Populate with your FAQ content using st.expander
        with st.expander("What is the ACE Questionnaire?"): st.write("The ACE (ARCOS Configuration Exploration) Questionnaire is a tool designed to gather detailed information about your utility company's callout processes...")
        with st.expander("How long does it take to complete?"): st.write("Typically 15-20 minutes, but you can save and resume.")
        # ... Add other FAQs from your previous app.py version ...

add_sidebar_ui()

if __name__ == "__main__":
    # Ensure necessary session state keys for questions/instructions are loaded if not already present
    # This is a fallback, primary loading should be within _initialize_session_state
    if 'questions' not in st.session_state:
        try: st.session_state.questions = load_questions('data/questions.txt')
        except: st.session_state.questions = []
    if 'instructions' not in st.session_state:
        try: st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
        except: st.session_state.instructions = ""
    main()