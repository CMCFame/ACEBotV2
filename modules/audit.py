# Add a new file: modules/audit.py

import os
import json
from datetime import datetime
import streamlit as st

class AuditLogger:
    def __init__(self, log_dir="secure/audit_logs"):
        """Initialize the audit logger."""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
        # Create a log file for today
        self.current_date = datetime.now().strftime("%Y-%m-%d")
        self.log_file = os.path.join(log_dir, f"audit_{self.current_date}.jsonl")
    
    def log_event(self, event_type, user=None, details=None, status="success"):
        """
        Log an event to the audit trail.
        
        Args:
            event_type: Type of event (access, data_change, auth, etc.)
            user: Username if authenticated, otherwise None
            details: Additional details about the event
            status: Outcome of the event (success, failure, error)
        """
        # Check if date has changed and update log file if needed
        current_date = datetime.now().strftime("%Y-%m-%d")
        if current_date != self.current_date:
            self.current_date = current_date
            self.log_file = os.path.join(self.log_dir, f"audit_{self.current_date}.jsonl")
        
        # Create the log entry
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "user": user if user else "anonymous",
            "ip_address": self._get_client_ip(),
            "details": details if details else {},
            "status": status,
            "session_id": st.session_state.get("session_id", "unknown")
        }
        
        # Write to log file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def _get_client_ip(self):
        """Get the client's IP address."""
        # Production implementation should extract IP from request headers
        return "127.0.0.1"
    
    def export_logs(self, start_date, end_date, event_types=None, users=None):
        """
        Export logs within a date range with optional filtering.
        
        Args:
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format
            event_types: List of event types to include, or None for all
            users: List of users to include, or None for all
            
        Returns:
            List of log entries matching criteria
        """
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Get all log files in the date range
        date_range = []
        current = start
        while current <= end:
            date_range.append(current.strftime("%Y-%m-%d"))
            current = current + timedelta(days=1)
        
        # Collect matching log entries
        entries = []
        for date_str in date_range:
            log_file = os.path.join(self.log_dir, f"audit_{date_str}.jsonl")
            if os.path.exists(log_file):
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            
                            # Apply filters
                            if event_types and entry["event_type"] not in event_types:
                                continue
                            if users and entry["user"] not in users:
                                continue
                                
                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        
        return entries