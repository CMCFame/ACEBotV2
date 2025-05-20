# modules/audit.py
import os
import json
from datetime import datetime

class AuditLogger:
    def __init__(self, log_dir="secure/audit_logs"):
        """Initialize the audit logger."""
        try:
            self.log_dir = log_dir
            os.makedirs(log_dir, exist_ok=True)
            
            # Create a log file for today
            self.current_date = datetime.now().strftime("%Y-%m-%d")
            self.log_file = os.path.join(log_dir, f"audit_{self.current_date}.jsonl")
        except Exception as e:
            print(f"Error initializing AuditLogger: {e}")
    
    def log_event(self, event_type, user=None, details=None, status="success"):
        """Log an event to the audit trail."""
        try:
            # Create the log entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "event_type": event_type,
                "user": user if user else "anonymous",
                "details": details if details else {},
                "status": status
            }
            
            # Write to log file
            with open(self.log_file, 'a') as f:
                f.write(json.dumps(log_entry) + "\n")
                
            print(f"AUDIT: {event_type} by {user or 'anonymous'} - {status}")
            return True
        except Exception as e:
            print(f"Error logging event: {e}")
            return False