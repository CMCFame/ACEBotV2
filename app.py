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
import re
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
          <p style="margin: 0; font-weight: 600; color: #004085; font-size: 15px;">❓ Next Question</p>
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
    """Check if the questionnaire is ready for summary generation using AI-driven assessment."""
    # Use AI-driven readiness check if available, fallback to legacy system
    if "question_tracker" in services:
        readiness = services["question_tracker"].is_ready_for_summary()
    else:
        # Fallback to legacy topic tracker
        readiness = services["topic_tracker"].check_summary_readiness()
    
    if not readiness["ready"]:
        warning_msg = readiness["message"]
        missing_info = readiness.get("missing_info", [])
        
        if missing_info:
            detailed_msg = f"Still need information about: {', '.join(missing_info[:3])}"
        else:
            detailed_msg = warning_msg
        
        st.session_state.visible_messages.append({
            "role": "assistant", 
            "content": f"I notice you'd like to see a summary, but let's make sure we have comprehensive coverage. {detailed_msg}\n\nLet's continue with a few more questions to ensure we have complete information for your ARCOS implementation."
        })
        
        st.session_state.chat_history.append({
            "role": "system",
            "content": f"User requested summary but questionnaire needs more coverage. {detailed_msg} Continue asking questions systematically to cover missing areas."
        })
        
        return False
    return True

def handle_summary_request():
    """Handle when user requests summary or AI indicates completion."""
    if check_summary_readiness():
        st.session_state.summary_requested = True
        return True
    return False

def add_debug_section():
    """Add debug section in sidebar for development."""
    if st.secrets.get("DEBUG_MODE", False):
        with st.sidebar:
            st.markdown("---")
            st.markdown("### Debug Controls")
            
            # Show loop detection status
            loop_count = len(st.session_state.get("conversation_loop_detector", []))
            st.write(f"Loop detector entries: {loop_count}")
            
            # Show answered questions
            answered_count = len(st.session_state.get("answered_questions", set()))
            total_questions = len(st.session_state.get("questions", []))
            st.write(f"Questions answered: {answered_count}/{total_questions}")
            
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

def process_user_input(processed_user_input):
    """AI-driven user input processing with structured response handling."""
    
    # Check for summary request first
    special_message = services["ai_service"].process_special_message_types(processed_user_input)
    if special_message["type"] == "summary_request":
        if handle_summary_request():
            st.rerun()
        return
    
    # Add user message to visible history
    st.session_state.visible_messages.append({"role": "user", "content": processed_user_input})
    
    # Create system instruction for AI-driven tracking
    tracking_instruction = (
        "\n\n[SYSTEM_INSTRUCTION: You MUST include QUESTION_TRACKING and COMPLETION_STATUS blocks in your response. "
        "If the user just provided an answer, mark answer_received: true and include their response text. "
        "Update your progress assessment and ask the next logical question from your systematic questionnaire coverage. "
        "Remember: Every response must include both structured tracking blocks.]"
    )
    
    guided_user_input = processed_user_input + tracking_instruction
    st.session_state.chat_history.append({"role": "user", "content": guided_user_input})
    
    # Get structured AI response
    ai_response_result = services["ai_service"].get_structured_response(st.session_state.chat_history)
    
    if not ai_response_result["success"]:
        # AI service failed - show error message
        error_message = "AI service is currently unavailable. Please try again later."
        st.session_state.visible_messages.append({"role": "assistant", "content": error_message})
        st.error(f"AI Service Error: {ai_response_result['error']}")
        return
    
    # Handle SUMMARY_REQUEST in raw response
    raw_response = ai_response_result["raw_response"]
    if "SUMMARY_REQUEST" in raw_response:
        if handle_summary_request():
            conversation_part = raw_response.split("SUMMARY_REQUEST")[0].strip()
            if conversation_part:
                # Extract display content without structured blocks
                display_content = services["ai_service"]._extract_display_content(conversation_part, {})
                st.session_state.chat_history.append({"role": "assistant", "content": display_content})
                st.session_state.visible_messages.append({"role": "assistant", "content": display_content})
            st.rerun()
        return
    
    # Process structured AI response data
    structured_data = ai_response_result["structured_data"]
    if structured_data:
        # Update question tracking using new system
        if "question_tracker" not in services:
            from modules.question_tracker import QuestionTracker
            services["question_tracker"] = QuestionTracker()
        
        processing_result = services["question_tracker"].process_ai_response(structured_data)
        
        # Log processing results for debugging
        if not processing_result["success"]:
            print(f"Question tracking processing errors: {processing_result['errors']}")
        if processing_result.get("warnings"):
            print(f"Question tracking warnings: {processing_result['warnings']}")
    
    # Process legacy TOPIC_UPDATE for backward compatibility
    if structured_data and structured_data.get("topic_update"):
        services["topic_tracker"].process_topic_update(raw_response)
    
    # Get display content (cleaned of structured blocks)
    display_content = ai_response_result["display_content"]
    
    # Add to conversation history
    if display_content:
        st.session_state.chat_history.append({"role": "assistant", "content": display_content})
        st.session_state.visible_messages.append({"role": "assistant", "content": display_content})
    
    # Extract user info if this is early in conversation
    extract_and_update_user_info(processed_user_input)
    
    # Validate response quality
    if structured_data:
        validation = services["ai_service"].validate_structured_response(structured_data)
        if not validation["is_valid"]:
            print(f"Response validation issues: {validation['missing_fields']}")
        if validation.get("warnings"):
            print(f"Response validation warnings: {validation['warnings']}")
    
    # Emergency fallback: if no question asked and not near completion, prompt AI
    if display_content and "?" not in display_content:
        progress_data = services["question_tracker"].get_progress_data() if "question_tracker" in services else {"ai_driven_progress": 0}
        if progress_data.get("ai_driven_progress", 0) < 90:  # Only force if not near completion
            print("Warning: AI didn't ask a question - may need fallback prompting")

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
        # Use topic tracker to get next question
        fallback = services["topic_tracker"].break_loop_with_next_question()
        st.session_state.chat_history.append({"role": "assistant", "content": fallback})
        st.session_state.visible_messages.append({"role": "assistant", "content": fallback})

def extract_and_update_user_info(user_input):
    """Extract user info if not already captured."""
    current_q_idx = st.session_state.get("current_question_index", 0)
    
    # Only extract user info if it's not already captured and it's early in the conversation
    if len(st.session_state.get("responses", [])) == 0 and not (st.session_state.user_info.get("name") or st.session_state.user_info.get("company")):
        user_info_data = services["ai_service"].extract_user_info(user_input)
        if user_info_data and (user_info_data.get("name") or user_info_data.get("company")):
            st.session_state.user_info = user_info_data
            user_context_msg = f"System note: User is {user_info_data.get('name', 'N/A')} from {user_info_data.get('company', 'N/A')}."
            if not any(m.get("content") == user_context_msg for m in st.session_state.chat_history if m.get("role")=="system"):
                st.session_state.chat_history.append({"role": "system", "content": user_context_msg})
    
    # Update response tracking
    questions_list = st.session_state.get("questions", [])
    current_official_question_text = st.session_state.get("current_question", questions_list[0] if questions_list else "")
    
    if current_q_idx < len(questions_list) and current_official_question_text:
        last_ai_msg_for_check = ""
        if st.session_state.visible_messages and st.session_state.visible_messages[-1]['role'] == 'assistant':
            last_ai_msg_for_check = st.session_state.visible_messages[-1]['content']
        
        is_answer = services["ai_service"].check_response_type(last_ai_msg_for_check or current_official_question_text, user_input)
        
        if is_answer:
            st.session_state.responses.append((current_official_question_text, user_input))
            st.session_state.current_question_index += 1
            if st.session_state.current_question_index < len(questions_list):
                st.session_state.current_question = questions_list[st.session_state.current_question_index]

def display_enhanced_completion_ui():
    """Enhanced completion UI with better summary validation."""
    if not st.session_state.get("summary_requested", False):
        return
    
    # Check readiness one more time using AI-driven assessment
    if "question_tracker" in services:
        readiness = services["question_tracker"].is_ready_for_summary()
    else:
        readiness = services["topic_tracker"].check_summary_readiness()
    
    if not readiness["ready"]:
        st.warning(f"Summary requested but questionnaire needs more coverage: {readiness['message']}")
        if st.button("Continue Questionnaire"):
            st.session_state.summary_requested = False
            st.rerun()
        return
    
    # Generate summary using AI-driven Q&A pairs if available
    if "question_tracker" in services:
        responses_list = services["question_tracker"].get_qa_pairs_for_export()
        # Still use summary generator for formatting, but with AI-driven data
        summary_text = services["summary_generator"].generate_conversation_summary()
    else:
        # Fallback to legacy system
        summary_text = services["summary_generator"].generate_conversation_summary()
        responses_list = services["summary_generator"].get_responses_as_list()
    
    # Show completion message
    st.success("✅ Questionnaire completed successfully!")
    st.info(f"Captured {len(responses_list)} question-answer pairs covering all major topic areas.")
    
    # Display summary in expandable section
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
    """Add the sidebar UI elements with KPI dashboard."""
    with st.sidebar:
        st.markdown("""
            <div style="text-align: center; margin-bottom: 25px;">
                <img src="https://www.publicpower.org/sites/default/files/logo-arcos_0.png"
                     alt="ARCOS Logo" style="max-width: 80%; height: auto; margin: 10px auto;" />
            </div>
        """, unsafe_allow_html=True)
        
        # KPI Dashboard - use AI-driven progress if available
        if "question_tracker" in services:
            try:
                progress_data = services["question_tracker"].get_progress_data()
                st.markdown("### 📊 AI-Driven Progress Dashboard")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("AI Progress", f"{progress_data.get('ai_driven_progress', 0)}%")
                with col2:
                    st.metric("Quality Score", f"{progress_data.get('quality_weighted_progress', 0)}%")
                
                col3, col4 = st.columns(2)
                with col3:
                    st.metric("Questions Asked", progress_data.get('questions_asked', 0))
                with col4:
                    st.metric("Questions Answered", progress_data.get('questions_answered', 0))
                    
            except (KeyError, AttributeError) as e:
                st.warning("Progress tracking initializing...")
                
        else:
            # Fallback to legacy progress tracking
            progress_data = services["topic_tracker"].get_progress_data()
            st.markdown("### 📊 Progress Dashboard")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Completion", f"{progress_data['percentage']}%")
            with col2:
                st.metric("Topics", f"{progress_data['covered_count']}/{progress_data['total_count']}")
            
            if 'questions_answered' in progress_data:
                st.metric("Questions Answered", progress_data['questions_answered'])
        
        # Show debug information if in debug mode
        if st.secrets.get("DEBUG_MODE", False):
            st.markdown("---")
            st.markdown("### 🔧 Debug Information")
            
            if "question_tracker" in services:
                debug_data = services["question_tracker"].debug_status()
                st.write(f"**AI Questions:** {debug_data['total_questions']}")
                st.write(f"**Current Question:** {debug_data['current_question']}")
                st.write(f"**Missing Info:** {len(debug_data.get('completion_status', {}).get('missing_critical_info', []))}")
                
            # Legacy debug info
            loop_entries = len(st.session_state.get("conversation_loop_detector", []))
            st.write(f"**Loop Entries:** {loop_entries}")
            
            answered_count = len(st.session_state.get("answered_questions", set()))
            st.write(f"**Legacy Answered:** {answered_count}")

        st.markdown("""
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
        
        # Resume functionality
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

def handle_example_request_with_progression():
    """Handle example requests while ensuring progression."""
    last_question_context = st.session_state.get("current_question", "the current topic")
    if st.session_state.visible_messages and st.session_state.visible_messages[-1]["role"] == "assistant":
        assistant_last_msg_content = st.session_state.visible_messages[-1]["content"]
        if "To continue with our question:" in assistant_last_msg_content:
            last_question_context = assistant_last_msg_content.split("To continue with our question:")[-1].strip()
        elif "?" in assistant_last_msg_content:
            last_question_context = assistant_last_msg_content

    if last_question_context:
        example_text_content = services["ai_service"].get_example_response(last_question_context)
        
        # Get NEXT question for progression
        current_q_idx = st.session_state.get("current_question_index", 0)
        questions_list = st.session_state.get("questions", [])
        next_question = "Let's continue with the next aspect of your callout process."
        
        if current_q_idx + 1 < len(questions_list):
            next_question = questions_list[current_q_idx + 1]
        
        formatted_example_display = create_example_html(example_text_content, next_question)
        
        st.session_state.visible_messages.append({"role": "user", "content": "Can you show me an example?"})
        st.session_state.visible_messages.append({"role": "assistant", "content": formatted_example_display})
        
        # Update current question index to move forward
        st.session_state.current_question_index = min(current_q_idx + 1, len(questions_list) - 1)
        if st.session_state.current_question_index < len(questions_list):
            st.session_state.current_question = questions_list[st.session_state.current_question_index]
        
        history_example_text = f"Example: {example_text_content}\n\nNext question:\n{next_question}"
        st.session_state.chat_history.append({"role": "user", "content": "Can you show me an example?"})
        st.session_state.chat_history.append({"role": "assistant", "content": history_example_text})
        
        return True
    return False

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
                
                # Initialize question tracker
                from modules.question_tracker import QuestionTracker
                services["question_tracker"] = QuestionTracker()
                
                # On first run, get the AI's welcome message using structured response
                initial_ai_input_messages = st.session_state.chat_history.copy() 
                ai_response_result = services["ai_service"].get_structured_response(initial_ai_input_messages)

                if ai_response_result["success"]:
                    # Process structured data from initial response
                    if ai_response_result["structured_data"]:
                        services["question_tracker"].process_ai_response(ai_response_result["structured_data"])
                    
                    # Get cleaned display content
                    cleaned_initial_response = ai_response_result["display_content"]
                    
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
        messages_count = len(st.session_state.get("visible_messages", []))
        if messages_count > 1 and not st.session_state.get("summary_requested", False):
            # Use AI-driven progress if available, fallback to legacy
            if "question_tracker" in services:
                progress_data = services["question_tracker"].get_progress_data()
            else:
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
            
            # Handle example button click with progression
            if st.session_state.example_button_clicked:
                st.session_state.example_button_clicked = False
                if handle_example_request_with_progression():
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
    
    # Initialize AI question tracking session state
    if 'ai_questions' not in st.session_state:
        st.session_state.ai_questions = {}
    if 'ai_question_sequence' not in st.session_state:
        st.session_state.ai_question_sequence = []
    if 'ai_completion_status' not in st.session_state:
        from config import TOPIC_AREAS
        st.session_state.ai_completion_status = {
            "overall_progress": 0,
            "topic_coverage": {topic: False for topic in TOPIC_AREAS.keys()},
            "missing_critical_info": [],
            "last_updated": ""
        }
    if 'ai_current_question' not in st.session_state:
        st.session_state.ai_current_question = None
    
    main()