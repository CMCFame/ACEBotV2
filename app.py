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
    </style>
    """, unsafe_allow_html=True)

def check_summary_readiness():
    """
    UNIFIED completion checker - eliminates competing validation systems.
    This is now the SINGLE source of truth for completion.
    """
    # Use the improved topic tracker validation
    readiness = services["topic_tracker"].check_summary_readiness()
    
    if not readiness["ready"]:
        # Give specific guidance instead of generic rejection
        if "missing_topics" in readiness:
            missing_list = readiness["missing_topics"]
            guidance_msg = f"Let's make sure we have complete information about: {', '.join(missing_list[:3])}. "
            
            # Add specific follow-up based on what's missing
            if "Calling Logistics" in missing_list:
                guidance_msg += "Could you clarify your union rules about calling employees simultaneously?"
            elif "Tiebreakers" in missing_list:
                guidance_msg += "What do you use to break ties when employees have equal overtime?"
            elif "Additional Rules" in missing_list:
                guidance_msg += "Are there any timing rules about when employees can be called?"
        else:
            guidance_msg = readiness["message"]
        
        st.session_state.visible_messages.append({
            "role": "assistant", 
            "content": guidance_msg
        })
        
        # Add system message to guide AI's next question
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"User wanted summary but missing: {readiness.get('message', 'some information')}. Ask specific follow-up questions to complete coverage."
        })
        
        return False
    return True

def handle_summary_request():
    """
    Simplified summary request handler - no more circular logic.
    """
    # First, try to auto-correct obvious validation errors
    corrections_made = services["topic_tracker"].force_completion_check()
    
    if corrections_made:
        print("Auto-corrected validation issues")
    
    # Now check if truly ready
    if check_summary_readiness():
        st.session_state.summary_requested = True
        return True
    return False

def add_debug_section():
    """Add debug section in sidebar for development."""
    if st.secrets.get("DEBUG_MODE", False):  # Only show in debug mode
        with st.sidebar:
            st.markdown("---")
            st.markdown("### Debug Controls")
            
            if st.button("🔍 Debug Q&A Extraction"):
                summary_gen = services["summary_generator"]
                qa_pairs = summary_gen._extract_qa_pairs_from_visible_messages()
                st.write(f"Extracted {len(qa_pairs)} Q&A pairs:")
                for i, (q, a) in enumerate(qa_pairs, 1):
                    st.write(f"{i}. Q: {q[:100]}...")
                    st.write(f"   A: {a[:100]}...")
            
            if st.button("📊 Show Topic Coverage"):
                coverage = st.session_state.get("topic_areas_covered", {})
                for topic, status in coverage.items():
                    st.write(f"{topic}: {'✅' if status else '❌'}")
            
            if st.button("🔄 Reset Topic Coverage"):
                services["topic_tracker"].force_topic_reset()
                st.success("All topics reset to incomplete")

def process_user_input(processed_user_input):
    """
    Enhanced user input processing with comprehensive answer recognition.
    """
    
    # Check for completion signals
    special_message = services["ai_service"].process_special_message_types(processed_user_input)
    if special_message["type"] == "summary_request":
        if handle_summary_request():
            st.rerun()
        return
    
    # Analyze if user provided comprehensive answer
    covered_topics = services["ai_service"].analyze_comprehensive_answer(processed_user_input)
    
    # Add user message to visible history
    st.session_state.visible_messages.append({"role": "user", "content": processed_user_input})
    
    # Create smart guidance based on coverage and comprehensive answers
    covered_count = sum(st.session_state.topic_areas_covered.values())
    total_count = len(st.session_state.topic_areas_covered)
    coverage_percentage = (covered_count / total_count) * 100
    
    # Build guidance message
    guidance_parts = [f"\n\n[SYSTEM_GUIDANCE: Progress {coverage_percentage:.0f}%."]
    
    if covered_topics:
        guidance_parts.append(f"User's answer may cover: {', '.join(covered_topics)}.")
        guidance_parts.append("Acknowledge comprehensive coverage and adapt accordingly.")
    
    if coverage_percentage >= 80:
        missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
        guidance_parts.append(f"Focus on final gaps: {', '.join(missing_topics)}.")
    else:
        guidance_parts.append("Continue with efficient, paired questions when appropriate.]")
    
    guiding_suffix = " ".join(guidance_parts)
    guided_user_input = processed_user_input + guiding_suffix
    st.session_state.chat_history.append({"role": "user", "content": guided_user_input})
    
    # Get AI response
    raw_ai_response = services["ai_service"].get_response(st.session_state.chat_history)
    
    # Handle AI completion signals
    if "SUMMARY_REQUEST" in raw_ai_response:
        if handle_summary_request():
            conversation_part = raw_ai_response.split("SUMMARY_REQUEST")[0].strip()
            if conversation_part:
                st.session_state.chat_history.append({"role": "assistant", "content": conversation_part})
                st.session_state.visible_messages.append({"role": "assistant", "content": conversation_part})
            st.rerun()
        return
    
    # Process TOPIC_UPDATE with better trust
    topic_updated = services["topic_tracker"].process_topic_update(raw_ai_response)
    
    # If AI indicated comprehensive coverage, update multiple topics
    if covered_topics and topic_updated:
        for topic in covered_topics:
            if topic in st.session_state.topic_areas_covered:
                st.session_state.topic_areas_covered[topic] = True
                print(f"Auto-updated {topic} based on comprehensive answer")
    
    # Clean response for display
    topic_update_pattern = r"TOPIC_UPDATE:\s*\{.*?\}"
    display_content = re.sub(topic_update_pattern, "", raw_ai_response, flags=re.DOTALL).strip()
    display_content = "\n".join([line for line in display_content.splitlines() if line.strip()])
    
    if display_content:
        st.session_state.chat_history.append({"role": "assistant", "content": display_content})
        st.session_state.visible_messages.append({"role": "assistant", "content": display_content})
    
    # Smart follow-up logic
    if not ("?" in display_content) and not st.session_state.get("summary_requested", False):
        # Check if we're near completion
        if coverage_percentage >= 75:
            force_completion_check()
        else:
            force_next_question()
    
    # Update user info
    extract_and_update_user_info(processed_user_input)

def force_completion_check():
    """Smart completion check when near end."""
    corrections_made = services["topic_tracker"].force_completion_check()
    readiness = services["topic_tracker"].check_summary_readiness()
    
    if readiness["ready"] or corrections_made:
        completion_msg = "Based on our conversation, I believe we've covered all essential aspects of your callout process. Is there anything unique to your operations that we haven't discussed?"
        st.session_state.chat_history.append({"role": "assistant", "content": completion_msg})
        st.session_state.visible_messages.append({"role": "assistant", "content": completion_msg})
    else:
        force_next_question()

def force_next_question():
    """Force the AI to ask the next question if it forgot to."""
    force_question_history = st.session_state.chat_history.copy()
    force_instruction = (
        "[CRITICAL SYSTEM TASK] Your previous response did not end with a question. "
        "Review the Complete Question Coverage Checklist in your instructions. "
        "Identify which specific question from the 45+ question checklist you need to ask next. "
        "Respond ONLY with that specific question - no apologies or explanations."
    )
    force_question_history.append({"role": "system", "content": force_instruction})
    next_question = services["ai_service"].get_response(force_question_history, max_tokens=150)
    
    if next_question and not next_question.startswith("Error:"):
        st.session_state.chat_history.append({"role": "assistant", "content": next_question})
        st.session_state.visible_messages.append({"role": "assistant", "content": next_question})
    else:
        # Fallback question
        fallback = "Could you please provide more details about your callout process?"
        st.session_state.chat_history.append({"role": "assistant", "content": fallback})
        st.session_state.visible_messages.append({"role": "assistant", "content": fallback})

def extract_and_update_user_info(user_input):
    """Enhanced user info extraction with smarter advancement."""
    current_q_idx = st.session_state.get("current_question_index", 0)
    
    # Extract user info early in conversation
    if len(st.session_state.get("responses", [])) <= 2 and not (st.session_state.user_info.get("name") or st.session_state.user_info.get("company")):
        user_info_data = services["ai_service"].extract_user_info(user_input)
        if user_info_data and (user_info_data.get("name") or user_info_data.get("company")):
            st.session_state.user_info = user_info_data
            user_context_msg = f"System note: User is {user_info_data.get('name', 'N/A')} from {user_info_data.get('company', 'N/A')}."
            if not any(m.get("content") == user_context_msg for m in st.session_state.chat_history if m.get("role")=="system"):
                st.session_state.chat_history.append({"role": "system", "content": user_context_msg})
    
    # Smart response tracking
    questions_list = st.session_state.get("questions", [])
    if current_q_idx < len(questions_list):
        last_ai_msg = ""
        if st.session_state.visible_messages and st.session_state.visible_messages[-2]['role'] == 'assistant':
            last_ai_msg = st.session_state.visible_messages[-2]['content']
        
        is_answer = services["ai_service"].check_response_type(last_ai_msg, user_input)
        
        if is_answer and len(user_input.strip()) > 10:  # Substantial answers only
            current_question = questions_list[current_q_idx] if current_q_idx < len(questions_list) else "General discussion"
            st.session_state.responses.append((current_question, user_input))
            st.session_state.current_question_index += 1
            
            if st.session_state.current_question_index < len(questions_list):
                st.session_state.current_question = questions_list[st.session_state.current_question_index]

def display_enhanced_completion_ui():
    """
    Simplified completion UI - no more competing validation.
    """
    if not st.session_state.get("summary_requested", False):
        return
    
    # One final validation check
    readiness = services["topic_tracker"].check_summary_readiness()
    
    if not readiness["ready"]:
        st.warning(f"Almost complete! Just need: {readiness['message']}")
        if st.button("Continue Questionnaire"):
            st.session_state.summary_requested = False
            st.rerun()
        return
    
    # Generate and display summary
    summary_text = services["summary_generator"].generate_conversation_summary()
    responses_list = services["summary_generator"].get_responses_as_list()
    
    st.success("✅ Questionnaire completed successfully!")
    st.info(f"Captured {len(responses_list)} question-answer pairs covering all essential topics.")
    
    # Rest of completion UI stays the same...
    with st.expander("📋 View Complete Summary", expanded=True):
        st.text_area("Summary", summary_text, height=400)
    
    # Download options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv_data = services["export_service"].generate_csv(responses_list)
        st.download_button(
            label="📥 Download CSV",
            data=csv_data,
            file_name=f"ACE_questionnaire_{st.session_state.user_info.get('company', 'response')}_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.download_button(
            label="📄 Download Summary",
            data=summary_text,
            file_name=f"ACE_summary_{st.session_state.user_info.get('company', 'response')}_{datetime.now().strftime('%Y%m%d')}.txt",
            mime="text/plain"
        )
    
    with col3:
        progress_report = services["summary_generator"].generate_progress_dashboard()
        st.download_button(
            label="📊 Download Report", 
            data=progress_report,
            file_name=f"ACE_report_{st.session_state.user_info.get('company', 'response')}_{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown"
        )
    
    # Email notification
    if not st.session_state.get("completion_email_sent", False):
        email_result = services["email_service"].send_notification(
            st.session_state.user_info, responses_list, services["export_service"], completed=True
        )
        if email_result["success"]:
            st.success("📧 Completion notification sent!")
        st.session_state.completion_email_sent = True

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
            dashboard_content = services["summary_generator"].generate_progress_dashboard()
            st.session_state.show_dashboard = True
            st.session_state.dashboard_content = dashboard_content
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
                st.session_state.app_initialized_first_run = True
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
                        st.session_state.app_initialized_first_run = True
                        st.rerun()
                    else:
                        st.error(result["message"])
            except Exception as e:
                st.error(f"Error processing file: {e}")
        
        # Add debug section
        add_debug_section()

def main():
    """Main application function."""
    tab1, tab2, tab3 = st.tabs(["Questionnaire", "Instructions", "FAQ"])

    with tab1:
        # Header, Logo, PII Warning
        st.markdown("""<div style="text-align: center; margin-bottom: 10px;"><img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png" alt="ARCOS Logo" style="max-width: 200px; height: auto;" /></div>""", unsafe_allow_html=True)
        st.markdown("""<div style="text-align: center; padding: 10px 0 20px 0;"><h1 style="color: #D22B2B; margin-bottom: 5px;">ACE Questionnaire</h1><p style="color: #555; font-size: 16px;">Help us understand your company's requirements for ARCOS implementation</p></div>""", unsafe_allow_html=True)
        st.warning("""**IMPORTANT: Data Privacy Notice** Please DO NOT enter any Personal Identifying Information (PII) such as social security numbers, home addresses, personal phone numbers, or other sensitive personal data. Focus on business processes, job roles, and organizational procedures only.""")
        
        # Initialize session state ONCE per session for the very first run
        if not st.session_state.get('app_initialized_first_run', False):
            try:
                services["session_manager"]._initialize_session_state() 
                
                # On first run, get the AI's welcome message
                initial_ai_input_messages = st.session_state.chat_history.copy() 
                initial_ai_response = services["ai_service"].get_response(initial_ai_input_messages)

                if initial_ai_response and not initial_ai_response.startswith("Error:") and not initial_ai_response.startswith("Bedrock client not initialized"):
                    # Clean the initial response
                    topic_update_pattern = r"TOPIC_UPDATE:\s*\{.*?\}"
                    cleaned_initial_response = re.sub(topic_update_pattern, "", initial_ai_response, flags=re.DOTALL).strip()
                    cleaned_initial_response = "\n".join([line for line in cleaned_initial_response.splitlines() if line.strip()])

                    if cleaned_initial_response:
                        st.session_state.chat_history.append({"role": "assistant", "content": cleaned_initial_response})
                        st.session_state.visible_messages.append({"role": "assistant", "content": cleaned_initial_response})
                else:
                    st.error(f"Failed to get initial greeting from AI. Details: {initial_ai_response}")
                    st.stop() 
                
                st.session_state.app_initialized_first_run = True
                st.rerun()

            except Exception as e:
                st.error(f"Error during initial application setup: {e}")
                st.stop()
        
        # Ensure other necessary session state variables are present
        if 'pending_example' not in st.session_state: st.session_state.pending_example = None
        if 'pending_help' not in st.session_state: st.session_state.pending_help = None
        if 'help_button_clicked' not in st.session_state: st.session_state.help_button_clicked = False
        if 'example_button_clicked' not in st.session_state: st.session_state.example_button_clicked = False

        # Display chat history
        for message in st.session_state.get("visible_messages", []):
            role = message.get("role")
            content = message.get("content","")
            if role == "user":
                user_label = st.session_state.user_info.get("name", "You") or "You"
                st.markdown(f"""<div style="display: flex; justify-content: flex-end; margin-bottom: 15px;"><div style="background-color: #e8f4f8; border-radius: 15px 15px 0 15px; padding: 12px 18px; max-width: 80%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #d1e7f0; border-right: 5px solid #4e8cff;"><p style="margin: 0; color: #0d467a; font-weight: 600; font-size: 15px;">{user_label}</p><p style="margin: 5px 0 0 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{content}</p></div></div>""", unsafe_allow_html=True)
            elif role == "assistant":
                st.markdown(f"""<div style="display: flex; margin-bottom: 15px;"><div style="background-color: #f8f9fa; border-radius: 15px 15px 15px 0; padding: 12px 18px; max-width: 85%; box-shadow: 2px 2px 4px rgba(0,0,0,0.1); border: 1px solid #e9ecef; border-left: 5px solid #6c757d;"><p style="margin: 0; color: #495057; font-weight: 600; font-size: 15px;">💬 Assistant</p><div style="margin-top: 8px;"><p style="margin: 0; white-space: pre-wrap; color: #333; line-height: 1.5;">{content}</p></div></div></div>""", unsafe_allow_html=True)
        
        # Show progress if beyond the very first AI message AND not in summary mode
        current_q_idx = st.session_state.get("current_question_index", 0)
        if (current_q_idx > 0 or (current_q_idx == 0 and len(st.session_state.get("visible_messages", [])) > 1)) and \
           not st.session_state.get("summary_requested", False):
            progress_data = services["topic_tracker"].get_progress_data()
            services["chat_ui"].display_progress_bar(progress_data)
        
        # Handle summary mode or active chat
        if st.session_state.get("summary_requested", False):
            display_enhanced_completion_ui()
        else: # Active chat mode
            def on_help_click(): st.session_state.help_button_clicked = True
            def on_example_click(): st.session_state.example_button_clicked = True
            
            buttons_col1, buttons_col2 = st.columns(2)
            with buttons_col1: st.button("Need help?", key="help_button_main_chat", on_click=on_help_click)
            with buttons_col2: st.button("Example", key="example_button_main_chat", on_click=on_example_click)
            
            # Handle help button click
            if st.session_state.help_button_clicked:
                st.session_state.help_button_clicked = False 
                last_question_context = st.session_state.get("current_question", "the current topic")
                if st.session_state.visible_messages and st.session_state.visible_messages[-1]["role"] == "assistant":
                     assistant_last_msg = st.session_state.visible_messages[-1]["content"]
                     if "?" in assistant_last_msg: last_question_context = assistant_last_msg

                temp_chat_history = st.session_state.chat_history + [{"role": "user", "content": f"I need help with this question: {last_question_context}"}]
                help_response_content = services["ai_service"].get_response(temp_chat_history)
                
                st.session_state.visible_messages.append({"role": "user", "content": "I need help with this question."})
                st.session_state.visible_messages.append({"role": "assistant", "content": help_response_content})
                st.session_state.chat_history.append({"role": "user", "content": f"I need help with this question: {last_question_context}"})
                st.session_state.chat_history.append({"role": "assistant", "content": help_response_content})
                st.rerun()
            
            # Handle example button click
            if st.session_state.example_button_clicked:
                st.session_state.example_button_clicked = False
                last_question_context = st.session_state.get("current_question", "the current topic")
                if st.session_state.visible_messages and st.session_state.visible_messages[-1]["role"] == "assistant":
                    assistant_last_msg_content = st.session_state.visible_messages[-1]["content"]
                    if "To continue with our question:" in assistant_last_msg_content:
                        last_question_context = assistant_last_msg_content.split("To continue with our question:")[-1].strip()
                    elif "?" in assistant_last_msg_content:
                        last_question_context = assistant_last_msg_content
                
                if last_question_context:
                    example_text_content = services["ai_service"].get_example_response(last_question_context)
                    formatted_example_display = create_example_html(example_text_content, last_question_context)
                    
                    st.session_state.visible_messages.append({"role": "user", "content": "Can you show me an example?"})
                    st.session_state.visible_messages.append({"role": "assistant", "content": formatted_example_display})
                    
                    history_example_text = f"Example: {example_text_content}\n\nTo continue with our question:\n{last_question_context}"
                    st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
                    st.session_state.chat_history.append({"role": "assistant", "content": history_example_text})
                    st.rerun()
                else:
                    st.error("Could not determine the current question to provide an example for.")

            # User input form
            with st.form(key='chat_form_main_input_key', clear_on_submit=True):
                user_input_val = st.text_input("Your response:", placeholder="Type your response or ask a question...", key="user_response_input_key")
                submit_button_val = st.form_submit_button("Send")
            
            processed_user_input = user_input_val if submit_button_val else None
            
            if processed_user_input:
                if not processed_user_input.strip():
                    st.error("Please enter a message before sending.")
                else:
                    process_user_input(processed_user_input)
                    st.rerun()

    with tab2:
        st.markdown("## How to Use the ACE Questionnaire")
        st.markdown("""
        Welcome to the ACE (ARCOS Configuration Exploration) Questionnaire! This interactive tool is designed to gather comprehensive information about your utility company's callout processes to help configure the ARCOS system for your specific needs.

        ### Getting Started
        1. **Begin the Conversation**: Simply start by providing your name and company when prompted
        2. **Answer Questions Thoroughly**: The AI will ask detailed questions about your callout procedures
        3. **Use Help Features**: If you're unsure about a question, click "Need help?" or "Example" for assistance
        4. **Save Your Progress**: Use the sidebar to save your session and continue later if needed

        ### What Information We Collect
        The questionnaire covers all essential aspects of your callout process:
        - **Basic Information**: Company details and callout types
        - **Staffing Details**: Number and roles of employees needed
        - **Contact Process**: Who you call first and communication methods
        - **List Management**: How you organize and traverse callout lists
        - **Insufficient Staffing**: Procedures when you can't fill all positions
        - **Calling Logistics**: Simultaneous calling and conditional responses
        - **List Changes**: How your lists update over time
        - **Tiebreakers**: Methods for breaking ties in overtime assignments
        - **Additional Rules**: Special scheduling and exception rules

        ### Tips for Success
        - **Be Specific**: Detailed answers help us configure ARCOS accurately
        - **Think Through Scenarios**: Consider different types of callouts you handle
        - **Include Variations**: Mention any exceptions or special procedures
        - **Ask for Examples**: Use the Example button to see what kind of detail we're looking for

        ### Privacy and Security
        - Do not include any Personal Identifying Information (PII)
        - Focus on business processes and organizational procedures
        - All data is used solely for ARCOS configuration purposes

        ### Completion and Next Steps
        Once all topics are covered, you'll receive:
        - A comprehensive summary of your responses
        - Downloadable files in multiple formats (CSV, text, detailed report)
        - Email notification to your implementation team (if configured)

        The information you provide will be used by ARCOS solution consultants to configure the system according to your specific union agreements, business rules, and operational procedures.
        """)
    
    with tab3:
        st.markdown("## Frequently Asked Questions")
        
        with st.expander("What is the ACE Questionnaire?"):
            st.write("""
            The ACE (ARCOS Configuration Exploration) Questionnaire is a tool designed to gather detailed information about your utility company's callout processes. This information is essential for properly configuring the ARCOS resource management system to match your specific operational needs, union agreements, and business rules.
            """)
        
        with st.expander("How long does it take to complete?"):
            st.write("""
            The questionnaire typically takes 15-20 minutes to complete, depending on the complexity of your callout processes. However, you can save your progress at any time and return to complete it later. The system will remember where you left off.
            """)
        
        with st.expander("What if I don't know an answer to a specific question?"):
            st.write("""
            If you're unsure about a question:
            1. Click the "Need help?" button for an explanation of what we're looking for
            2. Click the "Example" button to see a sample answer from a similar utility
            3. You can also consult with colleagues and return to complete the questionnaire later
            4. If a question doesn't apply to your operation, simply explain that in your response
            """)
        
        with st.expander("Is my information secure?"):
            st.write("""
            Yes, your information is handled securely and used only for ARCOS configuration purposes. We do not store Personal Identifying Information (PII). Please focus on business processes and avoid including personal data like social security numbers or home addresses.
            """)
        
        with st.expander("Can I save and resume my progress?"):
            st.write("""
            Absolutely! Use the "Save Progress" button in the sidebar to save your session. You'll receive a Session ID that you can use to resume later, or you can download a progress file. Your session includes all your previous responses and conversation history.
            """)
        
        with st.expander("What happens after I complete the questionnaire?"):
            st.write("""
            Once completed, you'll receive:
            - A comprehensive summary of all your responses
            - Downloadable files in multiple formats (CSV, text, detailed report)
            - An email notification will be sent to your ARCOS implementation team
            
            Your implementation consultant will use this information to configure ARCOS according to your specific requirements.
            """)
        
        with st.expander("What if our processes change after completing the questionnaire?"):
            st.write("""
            You can run through the questionnaire again at any time to capture changes in your processes. It's also helpful to inform your ARCOS implementation consultant of any significant changes to your callout procedures after the initial configuration.
            """)
        
        with st.expander("Do I need to complete this all at once?"):
            st.write("""
            No, you can save your progress and return later. The questionnaire is designed to be flexible. You might also want to gather input from different team members (dispatchers, supervisors, union representatives) before providing comprehensive answers.
            """)

# Add sidebar UI
add_sidebar_ui()

if __name__ == "__main__":
    # Ensure necessary session state keys for questions/instructions are loaded
    if 'questions' not in st.session_state:
        try: st.session_state.questions = load_questions('data/questions.txt')
        except: st.session_state.questions = []
    if 'instructions' not in st.session_state:
        try: st.session_state.instructions = load_instructions('data/prompts/system_prompt.txt')
        except: st.session_state.instructions = ""
    main()