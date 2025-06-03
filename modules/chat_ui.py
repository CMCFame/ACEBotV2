# modules/chat_ui.py - Simplified version for ACEBotV2
import streamlit as st
from datetime import datetime
import re
import html

class ChatUI:
    def __init__(self):
        """Initialize the chat UI components."""
        pass
    
    def display_chat_history(self):
        """Display the chat history with styled messages - simplified approach matching V3."""
        for message in st.session_state.visible_messages:
            # USER MESSAGES
            if message["role"] == "user":
                user_label = st.session_state.user_info.get("name", "You") or "You"
                st.markdown(
                    f"""
                    <div style="display: flex; justify-content: flex-end; margin-bottom: 10px;">
                      <div style="background-color: #e6f7ff; border-radius: 15px 15px 0 15px; padding: 10px 15px; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                        <p style="margin: 0; color: #333;"><strong>{user_label}</strong></p>
                        <p style="margin: 0; white-space: pre-wrap;">{message["content"]}</p>
                      </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # ASSISTANT MESSAGES
            elif message["role"] == "assistant":
                content = message["content"]
                
                # Check for example format (matching V3 style)
                if "*Example:" in content and "To continue with our question:" in content:
                    self._display_example_and_question(content)
                
                # Check for help responses
                elif any(word in content.lower() for word in ["help", "explanation", "understanding"]) and len(content) > 100:
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #17a2b8;">
                          <p style="margin: 0; color: #333;"><strong>💡 Help:</strong></p>
                          <p style="margin: 10px 0 0 0;">{content}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    
                # Welcome back messages
                elif "Welcome back!" in content and ("restored" in content or "resume" in content):
                    st.markdown(
                        f"""
                        <div style="display: flex; margin-bottom: 15px;">
                          <div style="background-color: #e8f4f8; border-radius: 15px 15px 15px 0; padding: 15px; max-width: 90%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1); border-left: 5px solid #4e8cff;">
                            <p style="margin: 0; color: #333;"><strong>Assistant</strong></p>
                            <div style="margin-top: 10px;">
                              <p style="margin: 0; white-space: pre-wrap; color: #0d6efd;">{content}</p>
                            </div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # Regular assistant messages
                else:
                    # Clean any HTML that might have slipped through
                    if "<" in content and ">" in content:
                        content = html.escape(content)
                    
                    st.markdown(
                        f"""
                        <div style="display: flex; margin-bottom: 10px;">
                          <div style="background-color: #f0f2f6; border-radius: 15px 15px 15px 0; padding: 10px 15px; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                            <p style="margin: 0; color: #333;"><strong>Assistant</strong></p>
                            <div style="margin-top: 5px;">
                              <p style="margin: 0; white-space: pre-wrap;">{content}</p>
                            </div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    
    def _display_example_and_question(self, content):
        """Display example and question with proper formatting - matching V3 style."""
        # Extract example and question parts
        example_text = ""
        question_text = ""
        
        if "*Example:" in content:
            # Extract example text
            example_start = content.find("*Example:") + 9
            example_end = content.find("*", example_start)
            if example_end != -1:
                example_text = content[example_start:example_end].strip()
            
            # Extract question part
            if "To continue with our question:" in content:
                question_start = content.find("To continue with our question:") + 31
                question_text = content[question_start:].strip()
        
        # Display in formatted boxes
        html_content = f"""
        <div style="display: flex; margin-bottom: 15px;">
          <div style="background-color: #f0f2f6; border-radius: 15px 15px 15px 0; padding: 15px; width: 90%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
            <p style="margin: 0; color: #333;"><strong>Assistant</strong></p>
        """
        
        # Add example box if we have example text
        if example_text:
            html_content += f"""
            <div style="background-color: #fff3cd; border-radius: 10px; padding: 15px; margin-top: 10px; margin-bottom: 15px; border: 1px solid #ffeeba; border-left: 5px solid #ffc107;">
              <p style="margin: 0; font-weight: bold; color: #856404;">📝 Example:</p>
              <p style="margin: 8px 0 0 0; color: #533f03; font-style: italic;">{example_text}</p>
            </div>
            """
        
        # Add question box if we have question text
        if question_text:
            html_content += f"""
            <div style="background-color: #e8f4ff; border-radius: 10px; padding: 15px; border-left: 5px solid #007bff;">
              <p style="margin: 0; font-weight: bold; color: #004085;">❓ Question:</p>
              <p style="margin: 8px 0 0 0; color: #0c5460;">{question_text}</p>
            </div>
            """
        
        html_content += """
          </div>
        </div>
        """
        
        st.markdown(html_content, unsafe_allow_html=True)
    
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
                        <div style="width: {progress_pct}%; height: 100%; background-color: #D22B2B; border-radius: 10px;"></div>
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
        # Add completion message
        st.markdown(
            """
            <div style="text-align: center; padding: 20px; background-color: #e8f5e8; border-radius: 10px; margin: 20px 0;">
                <h2 style="color: #2e7d32; margin-bottom: 10px;">
                    ✨ Questionnaire completed! ✨
                </h2>
                <p style="font-size: 16px; color: #1b5e20;">
                    Thank you for completing the ACE Questionnaire. Your responses will help us better understand your requirements.
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Add finalize button
        if not st.session_state.get("explicitly_finished", False):
            if st.button("✅ FINALIZE QUESTIONNAIRE", type="primary"):
                st.session_state.explicitly_finished = True
                st.rerun()
        
        # Show summary and download options after finalization
        if st.session_state.get("explicitly_finished", False):
            st.write("### Summary of Responses")
            st.text_area("Summary", summary_text, height=300)
            
            # Download options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                csv_data = export_service.generate_csv(responses)
                st.download_button(
                    label="📥 Download as CSV",
                    data=csv_data,
                    file_name=f"questionnaire_responses_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
            
            with col2:
                st.download_button(
                    label="📄 Download Summary",
                    data=summary_text,
                    file_name=f"ace_questionnaire_summary_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.txt",
                    mime="text/plain"
                )
                
            with col3:
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
            st.info("Please click the FINALIZE QUESTIONNAIRE button above to complete the process and view your summary.")