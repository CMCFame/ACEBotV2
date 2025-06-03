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

# Initialize services
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

def cleanup_html_messages():
    """Clean up any HTML content in existing messages."""
    import re
    
    if 'visible_messages' not in st.session_state:
        return
        
    cleaned_messages = []
    for msg in st.session_state.visible_messages:
        if msg["role"] == "assistant" and ("<div" in msg["content"] or "<p" in msg["content"]):
            content = msg["content"]
            
            # Try to extract clean text from HTML
            # Remove HTML tags
            clean_content = re.sub(r'<[^>]+>', '', content)
            
            # Clean up extra whitespace
            clean_content = re.sub(r'\s+', ' ', clean_content).strip()
            
            # If we can extract meaningful content, use it
            if len(clean_content) > 20:  # Arbitrary threshold for meaningful content
                msg["content"] = clean_content
        
        cleaned_messages.append(msg)
    
    st.session_state.visible_messages = cleaned_messages

def handle_help_request():
    """Handle help button clicks with improved error handling."""
    try:
        # Find the last question asked
        last_question = None
        for msg in reversed(st.session_state.visible_messages):
            if msg["role"] == "assistant" and "?" in msg["content"]:
                content = msg["content"]
                if "To continue with our question:" in content:
                    last_question = content.split("To continue with our question:")[-1].strip()
                else:
                    # Extract the last sentence with a question mark
                    sentences = content.split(".")
                    for sentence in reversed(sentences):
                        if "?" in sentence:
                            last_question = sentence.strip()
                            break
                break
        
        if not last_question:
            st.error("Could not find a question to provide help for.")
            return
        
        # Create help request messages
        help_messages = st.session_state.chat_history.copy()
        help_messages.append({
            "role": "user",
            "content": f"I need help understanding this question: {last_question}"
        })
        
        # Get help response
        help_response = services["ai_service"].get_response(help_messages)
        
        if help_response and not help_response.startswith("Error"):
            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": "I need help with this question"})
            st.session_state.chat_history.append({"role": "assistant", "content": help_response})
            st.session_state.visible_messages.append({"role": "user", "content": "I need help with this question"})
            st.session_state.visible_messages.append({"role": "assistant", "content": help_response})
        else:
            st.error("Could not get help response. Please try again.")
            
    except Exception as e:
        st.error(f"Error processing help request: {e}")

def handle_example_request():
    """Handle example button clicks with improved error handling."""
    try:
        # Find the last question asked
        last_question = None
        for msg in reversed(st.session_state.visible_messages):
            if msg["role"] == "assistant" and "?" in msg["content"]:
                content = msg["content"]
                # Skip messages that are HTML or contain raw HTML
                if "<div" in content or "<p" in content:
                    continue
                    
                if "To continue with our question:" in content:
                    last_question = content.split("To continue with our question:")[-1].strip()
                else:
                    # Extract the last sentence with a question mark
                    sentences = content.split(".")
                    for sentence in reversed(sentences):
                        if "?" in sentence:
                            last_question = sentence.strip()
                            break
                break
        
        if not last_question:
            st.error("Could not find a question to provide an example for.")
            return
        
        # Get example response
        example_text = services["ai_service"].get_example_response(last_question)
        
        if example_text and not example_text.startswith("Error") and not "<div" in example_text:
            # Create the properly formatted example message
            full_example_content = f"*Example: {example_text}*\n\nTo continue with our question:\n{last_question}"
            
            # Add to chat history
            st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
            st.session_state.chat_history.append({"role": "assistant", "content": full_example_content})
            st.session_state.visible_messages.append({"role": "user", "content": "Can you show me an example?"})
            st.session_state.visible_messages.append({"role": "assistant", "content": full_example_content})
        else:
            st.error("Could not get example response. Please try again.")
            
    except Exception as e:
        st.error(f"Error processing example request: {e}")
        print(f"DEBUG: Example request error: {e}")

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
                content = uploaded_file.read().decode("utf-8")
                
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
                st.session_state.questions = load_questions('data/questions.txt')
                st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
                services["session_manager"]._initialize_session_state()
                st.session_state.initialized = True
            except Exception as e:
                st.error(f"Error initializing session state: {e}")
                st.stop()
        
        # Clean up any HTML messages from previous versions
        cleanup_html_messages()
        
        # Display chat history
        services["chat_ui"].display_chat_history()
        
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
            # Add help/example buttons
            buttons_col1, buttons_col2 = st.columns(2)
            
            with buttons_col1:
                if st.button("Need help?", key="help_button"):
                    handle_help_request()
                    st.rerun()
            
            with buttons_col2:
                if st.button("Example", key="example_button"):
                    handle_example_request()
                    st.rerun()
            
            # User input form
            user_input = services["chat_ui"].add_input_form()
            
            if user_input:
                if not user_input or user_input.isspace():
                    st.error("Please enter a message before sending.")
                else:
                    # Process the user input
                    message_type = services["ai_service"].process_special_message_types(user_input)
                    
                    if message_type["type"] == "summary_request" or message_type["type"] == "frustration":
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.visible_messages.append({"role": "user", "content": user_input})
                        
                        force_summary = message_type["type"] == "frustration" or st.session_state.get("previous_summary_request", False)
                        st.session_state["previous_summary_request"] = True
                        
                        if force_summary:
                            st.session_state.summary_requested = True
                            for topic in st.session_state.topic_areas_covered: 
                                st.session_state.topic_areas_covered[topic] = True
                            summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                            st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
                            st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
                        else:
                            summary_readiness = services["topic_tracker"].check_summary_readiness()
                            if summary_readiness["ready"]:
                                st.session_state.summary_requested = True
                                summary_confirm = "I'll prepare a summary of your responses. You can download it below."
                                st.session_state.chat_history.append({"role": "assistant", "content": summary_confirm})
                                st.session_state.visible_messages.append({"role": "assistant", "content": summary_confirm})
                            else:
                                st.session_state.chat_history.append({"role": "assistant", "content": summary_readiness["message"]})
                                st.session_state.visible_messages.append({"role": "assistant", "content": summary_readiness["message"]})
                        st.rerun()
                        
                    else: # Regular input
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.visible_messages.append({"role": "user", "content": user_input})
                        
                        try:
                            # Get main AI response
                            ai_response_content = services["ai_service"].get_response(st.session_state.chat_history)
                            
                            # Validate AI response - ensure it's not HTML
                            if ai_response_content and ("<div" in ai_response_content or "<html" in ai_response_content):
                                print(f"WARNING: AI returned HTML content: {ai_response_content[:200]}...")
                                # Try to clean it up
                                import re
                                clean_content = re.sub(r'<[^>]+>', '', ai_response_content)
                                clean_content = re.sub(r'\s+', ' ', clean_content).strip()
                                
                                if len(clean_content) > 20:
                                    ai_response_content = clean_content
                                else:
                                    ai_response_content = "I apologize, but I encountered an issue generating my response. Could you please rephrase your question?"
                            
                            # Check if it's a topic update or regular response
                            is_topic_update = services["topic_tracker"].process_topic_update(ai_response_content)
                            
                            if not is_topic_update:
                                # Add regular response to chat
                                st.session_state.chat_history.append({"role": "assistant", "content": ai_response_content})
                                st.session_state.visible_messages.append({"role": "assistant", "content": ai_response_content})
                                
                                # Force topic update check
                                topic_check_messages = st.session_state.chat_history.copy()
                                topic_check_messages.append({
                                    "role": "user",
                                    "content": (
                                        "Based on the conversation, update topic coverage. "
                                        "Respond ONLY with: TOPIC_UPDATE: {\"basic_info\": true/false, "
                                        "\"staffing_details\": true/false, \"contact_process\": true/false, "
                                        "\"list_management\": true/false, \"insufficient_staffing\": true/false, "
                                        "\"calling_logistics\": true/false, \"list_changes\": true/false, "
                                        "\"tiebreakers\": true/false, \"additional_rules\": true/false}"
                                    )
                                })
                                
                                topic_update_response = services["ai_service"].get_response(topic_check_messages)
                                services["topic_tracker"].process_topic_update(topic_update_response)

                        except Exception as e:
                            st.error(f"An error occurred while processing AI response: {e}. Please try again.")
                            print(f"ERROR: AI response processing failed: {e}")
                            # Add a fallback message to keep conversation flowing
                            fallback_msg = "I'm sorry, I encountered a technical issue. Could you please repeat your last response?"
                            st.session_state.chat_history.append({"role": "assistant", "content": fallback_msg})
                            st.session_state.visible_messages.append({"role": "assistant", "content": fallback_msg})
                        
                        # Extract user info if this is the first response
                        if st.session_state.current_question_index == 0:
                            user_info_data = services["ai_service"].extract_user_info(user_input)
                            if user_info_data["name"] or user_info_data["company"]:
                                st.session_state.user_info = user_info_data
                        
                        # Update question tracking
                        if st.session_state.current_question_index < len(st.session_state.questions):
                            is_answer = services["ai_service"].check_response_type(st.session_state.current_question, user_input)
                            if is_answer:
                                st.session_state.responses.append((st.session_state.current_question, user_input))
                                st.session_state.current_question_index += 1
                                if st.session_state.current_question_index < len(st.session_state.questions):
                                    st.session_state.current_question = st.session_state.questions[st.session_state.current_question_index]
                        
                        st.rerun()

    with tab2:
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
        st.markdown("## Frequently Asked Questions")
        with st.expander("What is the ACE Questionnaire?"):
            st.write("The ACE (ARCOS Configuration Exploration) Questionnaire is a tool designed to gather detailed information about your utility company's callout processes. This information helps ARCOS solution consultants understand your specific requirements and configure the ARCOS system to match your existing workflows.")
        with st.expander("How long does it take to complete?"):
            st.write("The questionnaire typically takes 15-20 minutes to complete, depending on the complexity of your callout processes. You can save your progress at any time and return to complete it later.")
        with st.expander("Can I save my progress and continue later?"):
            st.write("Yes! Use the \"Save Progress\" button in the sidebar to save your current progress. You'll receive a Session ID that you can use to resume later. Make sure to save this ID in a safe place. You can also download a backup file if needed.")
        with st.expander("What if I don't know the answer to a question?"):
            st.write("If you're unsure about any question, click the \"Need help?\" button for a detailed explanation. If you still don't know, provide your best understanding and make a note that this area may need further discussion with your implementation consultant.")

add_sidebar_ui()

if __name__ == "__main__":
    main()