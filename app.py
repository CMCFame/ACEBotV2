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

def add_theme_toggle():
    """Add a theme toggle button to the bottom right corner."""
    # Default to light theme if not set
    if 'theme' not in st.session_state:
        st.session_state.theme = "light"
    
    # Add the CSS class based on current theme
    if st.session_state.theme == "dark":
        st.markdown("""
        <style>
        body {
            color-scheme: dark;
        }
        body, .main, [data-testid="stAppViewBlockContainer"] {
            background-color: #1e1e1e !important;
            color: #f0f0f0 !important;
        }
        .stTabs [data-baseweb="tab-list"] {
            background-color: #2d2d2d !important;
        }
        .stTabs [data-baseweb="tab"] {
            color: #f0f0f0 !important;
        }
        .stTabs [aria-selected="true"] {
            background-color: #3a3a3a !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        icon = "☀️"  # Sun icon for light mode
    else:
        icon = "🌙"  # Moon icon for dark mode
    
    # Add the theme toggle button
    st.markdown(f"""
    <div class="theme-toggle" onclick="toggleTheme()">
        <span class="theme-toggle-icon">{icon}</span>
    </div>
    
    <script>
    function toggleTheme() {{
        // Send message to Streamlit
        window.parent.postMessage({{
            type: "streamlit:setComponentValue",
            value: true,
            dataType: "bool",
            componentName: "theme_toggle"
        }}, "*");
    }}
    </script>
    """, unsafe_allow_html=True)
    
    # Create a hidden component to receive the click event
    theme_toggled = st.checkbox("Toggle Theme", key="theme_toggle", value=False, label_visibility="hidden")
    
    # Handle theme toggle
    if theme_toggled:
        # Toggle theme
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        # Reset checkbox
        st.session_state.theme_toggle = False
        # Force rerun to apply changes
        st.rerun()

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
                <p style="font-size: 0.9em; color: var(--text-secondary); margin-bottom: 20px;">
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
                    st.code(result["session_id"], language="")
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
            # Generate the progress dashboard artifact
            artifact = services["topic_tracker"].create_progress_dashboard_artifact()
            st.session_state.show_dashboard = True
            
            # Also generate a text version for the sidebar
            dashboard = services["summary_generator"].generate_progress_dashboard()
            st.session_state.dashboard_content = dashboard
            
            # Force a rerun to show the dashboard
            st.rerun()

        # Display dashboard if requested
        if st.session_state.get("show_dashboard", False):
            with st.expander("Progress Dashboard", expanded=True):
                # Use the artifacts function to create the React component
                try:
                    # Import and call the artifacts function
                    from antml.functions.artifacts import artifacts
                    artifact = services["topic_tracker"].create_progress_dashboard_artifact()
                    artifacts(
                        command=artifact["command"], 
                        id=artifact["id"], 
                        type=artifact["type"], 
                        title=artifact["title"], 
                        content=artifact["content"]
                    )
                except Exception as e:
                    # Fallback to text dashboard if artifacts function not available
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
    
    # Add theme toggle
    add_theme_toggle()

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
                <h1 style="color: var(--primary-red); margin-bottom: 5px;">ACE Questionnaire</h1>
                <p style="color: var(--text-secondary); font-size: 16px;">
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
        
        # Display chat history using the consolidated methods
        services["chat_ui"].display_chat_history()
        
        # Display any pending help or example content
        if st.session_state.pending_help:
            services["chat_ui"].render_help_message(st.session_state.pending_help)
            st.session_state.pending_help = None
            
        if st.session_state.pending_example:
            services["chat_ui"].render_example(
                st.session_state.pending_example["example_text"],
                st.session_state.pending_example["question_text"]
            )
            st.session_state.pending_example = None
        
        # Display progress bar if beyond first question
        if st.session_state.current_question_index > 0:
            progress_data = services["topic_tracker"].get_progress_data()
            services["chat_ui"].display_progress_bar(progress_data)
        
        # Show progress indicator during API requests
        services["chat_ui"].render_progress_indicator()
        
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
                
                # Begin API request
                st.session_state.api_request_in_progress = True
                
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
                    # Begin API request
                    st.session_state.api_request_in_progress = True
                    
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
                    
                    # Handle theme change requests
                    if message_type["type"] == "theme_request":
                        st.session_state.theme = message_type.get("theme", "light")
                        
                        # Add user message to chat history
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.visible_messages.append({"role": "user", "content": user_input})
                        
                        # Add assistant response
                        theme_name = "dark" if message_type.get("theme") == "dark" else "light"
                        response = f"I've switched to {theme_name} mode for you. Let me know if you need anything else!"
                        st.session_state.chat_history.append({"role": "assistant", "content": response})
                        st.session_state.visible_messages.append({"role": "assistant", "content": response})
                        
                        # Force rerun to apply theme
                        st.rerun()
                    
                    elif message_type["type"] == "example_request":
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
                            # Begin API request
                            st.session_state.api_request_in_progress = True
                            
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
                                st.session_state.visible_messages.append({"role": "assistant", "content": summary_readiness["message"]})
                        
                        st.rerun()
                        
                    elif message_type["type"] == "help_request":
                        # Handle help request
                        # Get the current question context
                        last_question = None
                        for msg in reversed(st.session_state.visible_messages):
                            if msg["role"] == "assistant" and "?" in msg["content"]:
                                last_question = msg["content"]
                                break
                        
                        if not last_question:
                            # Fallback to the last assistant message
                            for msg in reversed(st.session_state.visible_messages):
                                if msg["role"] == "assistant":
                                    last_question = msg["content"]
                                    break
                        
                        # Begin API request
                        st.session_state.api_request_in_progress = True
                        
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
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.chat_history.append({"role": "assistant", "content": help_response})
                        
                        # Add user message to visible messages
                        st.session_state.visible_messages.append({"role": "user", "content": user_input})
                        
                        # Save the help response to session state
                        st.session_state.pending_help = help_response
                        
                        # Force a rerun
                        st.rerun()
                        
                    else:
                        # Regular input - add to chat history
                        st.session_state.chat_history.append({"role": "user", "content": user_input})
                        st.session_state.visible_messages.append({"role": "user", "content": user_input})
                        
                        # Begin API request
                        st.session_state.api_request_in_progress = True
                        
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
                        
                        # Complete API request
                        st.session_state.api_request_in_progress = False
                        
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
        * **Theme Toggle** - Switch between light and dark mode using the toggle button in the bottom right
        
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
            
        with st.expander("Can I use this on my mobile device?"):
            st.write("""
            Yes! The ACE Questionnaire is fully mobile-responsive. You can complete it on your phone or tablet, 
            though a larger screen is recommended for the best experience. All features including saving progress 
            and theme toggling are available on mobile devices.
            """)
            
        with st.expander("How do I toggle between light and dark mode?"):
            st.write("""
            You can switch between light and dark mode by:
            
            1. Clicking the toggle button in the bottom right corner of the screen (moon/sun icon)
            2. Typing "dark mode" or "light mode" in the chat input
            
            Your theme preference will be saved as part of your session if you save your progress.
            """)

# Add sidebar UI
add_sidebar_ui()

# Run the main application
if __name__ == "__main__":
    main()