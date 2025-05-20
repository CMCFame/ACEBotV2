# Add new file: modules/emergency_access.py

import os
import json
from datetime import datetime, timedelta
import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class EmergencyAccessManager:
    def __init__(self, emergency_dir="secure/emergency"):
        """Initialize the emergency access manager."""
        self.emergency_dir = emergency_dir
        os.makedirs(emergency_dir, exist_ok=True)
        
        # Initialize access log
        self.access_log_file = os.path.join(emergency_dir, "emergency_access.jsonl")
        
        # Initialize breach notification settings
        self.settings_file = os.path.join(emergency_dir, "settings.json")
        if os.path.exists(self.settings_file):
            with open(self.settings_file, 'r') as f:
                self.settings = json.load(f)
        else:
            # Default settings
            self.settings = {
                "notification_recipients": [],
                "breach_notification_template": """
                IMPORTANT: POTENTIAL DATA BREACH NOTIFICATION
                
                Date/Time: {timestamp}
                Detected by: {detected_by}
                
                Description: {description}
                
                Potentially affected data:
                {affected_data}
                
                Immediate actions taken:
                {immediate_actions}
                
                Next steps:
                {next_steps}
                
                This notification is being sent in compliance with HIPAA breach notification requirements.
                
                For more information, please contact:
                {contact_info}
                """,
                "emergency_contacts": []
            }
            self._save_settings()
    
    def _save_settings(self):
        """Save settings to file."""
        with open(self.settings_file, 'w') as f:
            json.dump(self.settings, f, indent=2)
    
    def log_emergency_access(self, username, reason, accessed_data):
        """Log emergency access to PHI."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "reason": reason,
            "accessed_data": accessed_data,
            "ip_address": self._get_client_ip()
        }
        
        with open(self.access_log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
        
        # Also notify emergency contacts
        self._notify_emergency_access(log_entry)
        
        return {"success": True, "message": "Emergency access logged and notifications sent."}
    
    def _notify_emergency_access(self, log_entry):
        """Notify emergency contacts of emergency access."""
        # Only proceed if there are emergency contacts
        if not self.settings["emergency_contacts"]:
            return
        
        # Create notification message
        subject = f"EMERGENCY ACCESS ALERT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        body = f"""
        ALERT: Emergency Access to PHI
        
        Time: {log_entry['timestamp']}
        User: {log_entry['username']}
        Reason: {log_entry['reason']}
        Data Accessed: {log_entry['accessed_data']}
        IP Address: {log_entry['ip_address']}
        
        This notification is sent automatically. Please investigate this access immediately.
        """
        
        # Send email to all emergency contacts
        for contact in self.settings["emergency_contacts"]:
            self._send_email(contact, subject, body)
    
    def _get_client_ip(self):
        """Get the client's IP address."""
        # This is a simplified version - in production use proper IP extraction
        return "127.0.0.1"
    
    def _send_email(self, recipient, subject, body):
        """Send an email notification."""
        # Get email settings from Streamlit secrets
        sender_email = st.secrets.get("EMAIL_SENDER", "")
        sender_password = st.secrets.get("EMAIL_PASSWORD", "")
        
        if not sender_email or not sender_password:
            return {"success": False, "message": "Email configuration incomplete"}
        
        try:
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP('smtp.gmail.com', 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            server.quit()
            
            return {"success": True, "message": "Email sent successfully"}
        except Exception as e:
            return {"success": False, "message": f"Failed to send email: {e}"}
    
# Continuing from the report_data_breach method:

    def report_data_breach(self, detected_by, description, affected_data, immediate_actions, next_steps, contact_info):
        """Report a potential data breach and send notifications."""
        # Create breach report
        breach_id = f"breach_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        breach_report = {
            "breach_id": breach_id,
            "timestamp": datetime.now().isoformat(),
            "detected_by": detected_by,
            "description": description,
            "affected_data": affected_data,
            "immediate_actions": immediate_actions,
            "next_steps": next_steps,
            "contact_info": contact_info,
            "notification_sent": False,
            "notification_time": None
        }
        
        # Save the report
        report_file = os.path.join(self.emergency_dir, f"{breach_id}.json")
        with open(report_file, 'w') as f:
            json.dump(breach_report, f, indent=2)
        
        # Send notifications
        notification_result = self._send_breach_notifications(breach_report)
        
        # Update the report with notification status
        breach_report["notification_sent"] = notification_result["success"]
        breach_report["notification_time"] = datetime.now().isoformat()
        
        with open(report_file, 'w') as f:
            json.dump(breach_report, f, indent=2)
        
        return {
            "success": True,
            "message": "Data breach reported and notifications sent.",
            "breach_id": breach_id,
            "notification_result": notification_result
        }
    
    def _send_breach_notifications(self, breach_report):
        """Send breach notifications to all configured recipients."""
        if not self.settings["notification_recipients"]:
            return {"success": False, "message": "No notification recipients configured"}
        
        # Format the notification message
        notification_message = self.settings["breach_notification_template"].format(
            timestamp=breach_report["timestamp"],
            detected_by=breach_report["detected_by"],
            description=breach_report["description"],
            affected_data=breach_report["affected_data"],
            immediate_actions=breach_report["immediate_actions"],
            next_steps=breach_report["next_steps"],
            contact_info=breach_report["contact_info"]
        )
        
        subject = f"URGENT: Data Breach Notification - {datetime.now().strftime('%Y-%m-%d')}"
        
        # Send to all recipients
        success_count = 0
        for recipient in self.settings["notification_recipients"]:
            result = self._send_email(recipient, subject, notification_message)
            if result["success"]:
                success_count += 1
        
        if success_count == len(self.settings["notification_recipients"]):
            return {"success": True, "message": f"Notifications sent to all {success_count} recipients"}
        elif success_count > 0:
            return {
                "success": True, 
                "message": f"Notifications sent to {success_count} of {len(self.settings['notification_recipients'])} recipients"
            }
        else:
            return {"success": False, "message": "Failed to send notifications"}
    
    def update_notification_settings(self, new_settings):
        """Update breach notification settings."""
        if "notification_recipients" in new_settings:
            self.settings["notification_recipients"] = new_settings["notification_recipients"]
            
        if "breach_notification_template" in new_settings:
            self.settings["breach_notification_template"] = new_settings["breach_notification_template"]
            
        if "emergency_contacts" in new_settings:
            self.settings["emergency_contacts"] = new_settings["emergency_contacts"]
        
        self._save_settings()
        
        return {"success": True, "message": "Notification settings updated"}
    
    def get_breach_reports(self, limit=10):
        """Get the most recent breach reports."""
        reports = []
        
        for filename in os.listdir(self.emergency_dir):
            if filename.startswith("breach_") and filename.endswith(".json"):
                file_path = os.path.join(self.emergency_dir, filename)
                try:
                    with open(file_path, 'r') as f:
                        report = json.load(f)
                        reports.append(report)
                except Exception:
                    continue
        
        # Sort by timestamp (newest first)
        reports.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        # Limit the number of reports
        return reports[:limit]