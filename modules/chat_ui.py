# modules/chat_ui.py
import streamlit as st
from datetime import datetime

class ChatUI:
    def __init__(self):
        """Initialize the chat UI components."""
        pass
    
    def display_chat_history(self):
        """Display the chat history with styled messages."""
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

                # HELP BOX
                if "I need help with this question" in content:
                    help_text = content.replace("I need help with this question", "").strip()
                    st.markdown(
                        f"""
                        <div style="background-color: #f8f9fa; border-radius: 10px; padding: 15px; margin-bottom: 15px; border-left: 5px solid #17a2b8;">
                          <p style="margin: 0; color: #333;"><strong>💡 Help:</strong></p>
                          <p style="margin: 10px 0 0 0;">{help_text}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # EXAMPLE BOX
                elif "*Example:" in content or content.strip().startswith("Example:"):
                    # Extract example and question text
                    if "*Example:" in content:
                        example_parts = content.split("*Example:")
                        if len(example_parts) > 1:
                            example_text = example_parts[1].split("*")[0].strip()
                            remainder = example_parts[1].split("*", 1)[1] if len(example_parts[1].split("*")) > 1 else ""
                            
                            if "To continue with our question" in remainder:
                                question_text = remainder.split("To continue with our question", 1)[1].strip()
                            else:
                                question_text = remainder.strip()
                    else:
                        example_parts = content.split("Example:", 1)
                        example_text = example_parts[1].strip() if len(example_parts) > 1 else ""
                        question_text = ""

                    # Only display the example box, don't repeat the question separately                    
                    st.markdown(
                        f"""
                        <div style="display: flex; margin-bottom: 15px;">
                          <div style="background-color: #f0f2f6; border-radius: 15px 15px 15px 0; padding: 15px; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                            <p style="margin: 0; color: #333;"><strong>Assistant</strong></p>
                            <div style="background-color: #fff3cd; border-radius: 10px; padding: 10px; margin: 10px 0; border-left: 5px solid #ffc107;">
                              <p style="margin: 0;"><strong>📝 Example:</strong> <i>{example_text}</i></p>
                            </div>
                            {f'<p style="margin: 10px 0 0 0; font-weight: bold; color: #0c5460;">{question_text}</p>' if question_text else ''}
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                # REGULAR ASSISTANT MESSAGE
                else:
                    # Highlight questions within the message by bolding text that ends with '?'
                    # But don't create separate message blocks
                    parts = []
                    current_part = ""
                    for sentence in content.split(". "):
                        if sentence.strip().endswith("?"):
                            # This is a question sentence - add it with formatting
                            if current_part:
                                parts.append(f"<p style='margin: 5px 0;'>{current_part}</p>")
                                current_part = ""
                            parts.append(f"<p style='margin: 5px 0; font-weight: bold; color: #198754;'>{sentence.strip()}.</p>")
                        else:
                            # This is a regular sentence - add to current part
                            if current_part:
                                current_part += ". " + sentence.strip()
                            else:
                                current_part = sentence.strip()
                    
                    # Add any remaining text
                    if current_part:
                        parts.append(f"<p style='margin: 5px 0;'>{current_part}</p>")
                    
                    # Join all parts and display as one message
                    formatted_content = "".join(parts)
                    
                    st.markdown(
                        f"""
                        <div style="display: flex; margin-bottom: 10px;">
                          <div style="background-color: #f0f2f6; border-radius: 15px 15px 15px 0; padding: 10px 15px; max-width: 80%; box-shadow: 1px 1px 3px rgba(0,0,0,0.1);">
                            <p style="margin: 0; color: #333;"><strong>Assistant</strong></p>
                            <div style="margin-top: 5px;">
                              {formatted_content}
                            </div>
                          </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
    
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