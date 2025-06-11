# modules/email_service.py
import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from datetime import datetime
from config import EMAIL_CONFIG

class EmailService:
    def __init__(self):
        """Initialize the email service using configuration from Streamlit secrets."""
        # Get email settings from secrets
        self.sender_email = st.secrets.get(EMAIL_CONFIG["SENDER_KEY"], "")
        self.sender_password = st.secrets.get(EMAIL_CONFIG["PASSWORD_KEY"], "")
        self.recipient_email = st.secrets.get(EMAIL_CONFIG["RECIPIENT_KEY"], "")
        self.smtp_server = st.secrets.get(EMAIL_CONFIG["SMTP_SERVER_KEY"], EMAIL_CONFIG["DEFAULT_SMTP_SERVER"])
        self.smtp_port = st.secrets.get(EMAIL_CONFIG["SMTP_PORT_KEY"], EMAIL_CONFIG["DEFAULT_SMTP_PORT"])
        
    def is_configured(self):
        """Check if email service is properly configured."""
        return bool(self.sender_email and self.sender_password and self.recipient_email)
    
    def send_notification(self, user_info, answers, export_service, completed=False):
        """Send an email notification with attached response data."""
        if not self.is_configured():
            return {"success": False, "message": "Email configuration not complete. Notification email not sent."}
            
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.sender_email
            msg['To'] = self.recipient_email
            
            # Set subject based on whether questionnaire was completed
            status = "completed" if completed else "in progress"
            msg['Subject'] = f"ACE Questionnaire {status} - {user_info['name']} from {user_info['company']}"
            
            # Create email body
            body = f"""
            <html>
            <body>
            <h2>ACE Questionnaire Submission</h2>
            <p><strong>Status:</strong> {"Completed" if completed else "In Progress"}</p>
            <p><strong>User:</strong> {user_info['name']}</p>
            <p><strong>Company:</strong> {user_info['company']}</p>
            <p><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </body>
            </html>
            """
            msg.attach(MIMEText(body, 'html'))
            
            # Create and attach CSV file
            csv_data = export_service.generate_csv(answers)
            attachment = MIMEApplication(csv_data)
            attachment.add_header('Content-Disposition', 'attachment', 
                                filename=f"ACE_Questionnaire_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.csv")
            msg.attach(attachment)
            
            # Try to also attach Excel file if available
            try:
                excel_data = export_service.generate_excel(answers)
                # Skip if we got CSV back instead (fallback when Excel libs aren't available)
                if not excel_data[:10].decode('utf-8', errors='ignore').startswith("Question,Answer"):
                    excel_attachment = MIMEApplication(excel_data)
                    excel_attachment.add_header('Content-Disposition', 'attachment', 
                                    filename=f"ACE_Questionnaire_{user_info['company']}_{datetime.now().strftime('%Y%m%d')}.xlsx")
                    msg.attach(excel_attachment)
            except Exception:
                # Excel format failed, but we already have CSV, so continue
                pass
                
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.send_message(msg)
            
            return {"success": True, "message": f"Email notification sent to {self.recipient_email}"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send email: {e}"}