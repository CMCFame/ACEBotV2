# modules/chat_ui.py
import streamlit as st
from datetime import datetime
import re
import html

class ChatUI:
    def __init__(self):
        """Initialize the chat UI components."""
        pass
    
    def display_chat_history(self):
        """Display the chat history with styled messages and improved example formatting."""
        for message in st.session_state.visible_messages:
            # Skip messages that have been directly displayed already
            if message.get("already_displayed"):
                continue
                
            # Render message based on type
            if message["role"] == "user":
                self.render_user_message(message)
            elif message["role"] == "assistant":
                self._render_assistant_message(message)
    
    def render_user_message(self, message):
        """Render a user message with consistent styling."""
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
        
    def _render_assistant_message(self, message):
        """Route assistant message to appropriate renderer based on content."""
        content = message["content"]
        
        # Help box
        if "I need help with this question" in content:
            self.render_help_message(content)
        # Welcome back message (session restoration)
        elif "Welcome back!" in content and "I've restored your previous session" in content:
            self.render_welcome_back_message(content)
        # Example message with special formatting
        elif "*Example:" in content or "Example:" in content:
            self._display_example_and_question(content)
        # Regular assistant message
        else:
            self.render_assistant_message(content)

    def render_assistant_message(self, content):
        """Render a standard assistant message."""
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
        
    def render_help_message(self, content):
        """Render a help message with special styling."""
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
    
    def render_welcome_back_message(self, content):
        """Render a welcome back message with special styling."""
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
    
    def render_example(self, example_text, question_text):
        """Render an example and question box with enhanced styling."""
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

        # Mark this as displayed in the UI
        st.session_state.visible_messages.append({
            "role": "assistant", 
            "content": f"Example: {example_text}\n\nTo continue with our question:\n{question_text}",
            "already_displayed": True
        })
    
    def _display_example_and_question(self, content):
        """
        Display example and question with enhanced visual separation.
        Uses a simplified parsing approach for better compatibility.
        """
        # Extract example content using basic string operations
        example_text = ""
        question_text = ""
        
        # Find example part
        if "*Example:" in content:
            parts = content.split("*Example:", 1)
            if len(parts) > 1:
                example_parts = parts[1].split("*", 1)
                if len(example_parts) > 1:
                    example_text = example_parts[0].strip()
                    remaining = example_parts[1].strip()
                else:
                    example_text = example_parts[0].strip()
                    remaining = ""
            else:
                remaining = content
        elif "Example:" in content:
            parts = content.split("Example:", 1)
            if len(parts) > 1:
                example_text = parts[1].strip()
                remaining = ""
                
                # Try to find where example ends and question begins
                if "To continue with our question" in example_text:
                    example_parts = example_text.split("To continue with our question", 1)
                    example_text = example_parts[0].strip()
                    if len(example_parts) > 1:
                        question_text = "To continue with our question" + example_parts[1].strip()
            else:
                remaining = content
        else:
            remaining = content
            
        # If we already have question text from above, use it
        if not question_text and "To continue with our question" in remaining:
            parts = remaining.split("To continue with our question", 1)
            if len(parts) > 1:
                question_text = parts[1].strip()
        
        # If still no question found, look for a sentence with a question mark
        if not question_text:
            sentences = remaining.split(". ")
            for sentence in reversed(sentences):
                if "?" in sentence:
                    question_text = sentence.strip()
                    break
                    
        # If still no question, use all remaining text
        if not question_text and remaining:
            question_text = remaining
        
        # Use the specialized example renderer
        self.render_example(example_text, question_text)
    
    def add_help_example_buttons(self):
        """Add help and example buttons."""
        buttons_col1, buttons_col2 = st.columns(2)
        
        with buttons_col1:
            help_button = st.button("Need help?", key="help_button")
        
        with buttons_col2:
            example_button = st.button("Example", key="example_button")
            
        return help_button, example_button
    
    def add_input_form(self):
        """Add the chat input form."""
        with st.form(key='chat_form', clear_on_submit=True):
            user_input = st.text_input("Your response:", placeholder="Type your response or ask a question...")
            submit_button = st.form_submit_button("Send")
            
        return user_input if submit_button else None
    
    def display_progress_bar(self, progress_data):
        """Display a progress bar showing topic coverage."""
        progress_pct = progress_data["percentage"]
        covered_count = progress_data["covered_count"]
        total_count = progress_data["total_count"]
        
        st.markdown(
            f"""
            <div style="margin: 20px 0;">
                <div style="display: flex; align-items: center; margin-bottom: 5px;">
                    <div style="flex-grow: 1; height: 20px; background-color: #f0f2f6; border-radius: 10px; overflow: hidden;">
                        <div style="width: {progress_pct}%; height: 100%; background-color: var(--primary-red); border-radius: 10px;"></div>
                    </div>
                    <div style="margin-left: 10px; font-weight: bold;">{progress_pct}%</div>
                </div>
                <p style="text-align: center; margin: 0; color: #555;">
                    {covered_count} of {total_count} topic areas covered
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def display_completion_ui(self, summary_text, export_service, user_info, responses):
        """Display completion UI with summary and download options."""
        # Add a more explicit completion message with button
        st.markdown(
            """
            <div style="text-align: center; padding: 20px; background-color: var(--light-red); border-radius: 10px; margin: 20px 0;">
                <h2 style="color: var(--primary-red); margin-bottom: 10px;">
                    ✨ Questionnaire completed! ✨
                </h2>
                <p style="font-size: 16px; color: #1b5e20;">
                    Thank you for completing the ACE Questionnaire. Your responses will help us better understand your requirements.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Add a clear finish button above the summary
        if not st.session_state.get("explicitly_finished", False):
            if st.button("✅ FINALIZE QUESTIONNAIRE", type="primary"):
                st.session_state.explicitly_finished = True
                st.rerun()
        
        # Only show summary after explicit finalization
        if st.session_state.get("explicitly_finished", False):
            # Display summary in a text area
            st.write("### Summary of Responses")
            st.text_area("Summary", summary_text, height=300)
            
            # Provide download options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Generate CSV for download
                csv_data = export_service.generate_csv(responses)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name=f"questionnaire_responses_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                # Download formatted summary
                st.download_button(
                    label="📄 Download Summary",
                    data=summary_text,
                    file_name=f"ace_questionnaire_summary_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                
            with col3:
                # Download full progress report
                from modules.summary import SummaryGenerator
                summary_gen = SummaryGenerator()
                progress_dashboard = summary_gen.generate_progress_dashboard()
                st.download_button(
                    label="📊 Download Full Report",
                    data=progress_dashboard,
                    file_name=f"ace_complete_report_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.md",
                    mime="text/markdown"
                )
        else:
            # Provide a brief instruction and the finalize button
            st.info("Please click the FINALIZE QUESTIONNAIRE button above to complete the process and view your summary.")
    
    def render_progress_indicator(self):
        """Render a subtle progress indicator during API requests."""
        if st.session_state.get("api_request_in_progress", False):
            st.markdown(
                """
                <div style="display: flex; justify-content: center; margin: 15px 0;">
                    <div style="display: flex; align-items: center; background-color: #f8f9fa; padding: 8px 15px; border-radius: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                        <div class="loading-spinner"></div>
                        <span style="margin-left: 10px; color: #555;">Thinking...</span>
                    </div>
                </div>
                <style>
                    .loading-spinner {
                        width: 18px;
                        height: 18px;
                        border: 3px solid #eee;
                        border-top: 3px solid #3498db;
                        border-radius: 50%;
                        animation: spin 1s linear infinite;
                    }
                    @keyframes spin {
                        0% { transform: rotate(0deg); }
                        100% { transform: rotate(360deg); }
                    }
                </style>
                """,
                unsafe_allow_html=True
            )