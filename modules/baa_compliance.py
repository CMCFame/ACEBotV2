# Add new file: modules/baa_compliance.py

import os
import json
from datetime import datetime
import streamlit as st

class BAAComplianceManager:
    def __init__(self, baa_dir="secure/baa"):
        """Initialize the BAA compliance manager."""
        self.baa_dir = baa_dir
        os.makedirs(baa_dir, exist_ok=True)
        
        # Load BAA information if available
        self.baa_file = os.path.join(baa_dir, "baa_info.json")
        if os.path.exists(self.baa_file):
            with open(self.baa_file, 'r') as f:
                self.baa_info = json.load(f)
        else:
            # Initialize with empty data
            self.baa_info = {
                "is_active": False,
                "covered_entity": "",
                "business_associate": "ARCOS LLC",
                "effective_date": None,
                "expiration_date": None,
                "last_review_date": None,
                "data_handling_requirements": {
                    "encryption_required": True,
                    "access_controls_required": True,
                    "audit_logging_required": True,
                    "retention_period_days": 730,  # 2 years
                    "breach_notification_window_hours": 24
                },
                "authorized_personnel": []
            }
            self._save_baa_info()
    
    def _save_baa_info(self):
        """Save BAA information to file."""
        with open(self.baa_file, 'w') as f:
            json.dump(self.baa_info, f, indent=2)
    
    def update_baa_info(self, new_info):
        """Update BAA information."""
        # Validate required fields
        required_fields = ["covered_entity", "effective_date", "expiration_date"]
        for field in required_fields:
            if field not in new_info or not new_info[field]:
                return {"success": False, "message": f"Missing required field: {field}"}
        
        # Update BAA info with new data
        for key, value in new_info.items():
            if key in self.baa_info:
                self.baa_info[key] = value
        
        # Set is_active based on dates
        effective = datetime.fromisoformat(self.baa_info["effective_date"])
        expiration = datetime.fromisoformat(self.baa_info["expiration_date"])
        now = datetime.now()
        
        self.baa_info["is_active"] = effective <= now <= expiration
        
        # Save updated info
        self._save_baa_info()
        
        # Log the update
        self._log_baa_action("update", f"BAA information updated by {st.session_state.get('user', {}).get('username', 'system')}")
        
        return {"success": True, "message": "BAA information updated successfully"}
    
    def check_baa_status(self):
        """Check if BAA is active and valid."""
        if not self.baa_info["is_active"]:
            return {"status": "inactive", "message": "BAA is not active."}
        
        # Check expiration date
        expiration = datetime.fromisoformat(self.baa_info["expiration_date"])
        now = datetime.now()
        
        if now > expiration:
            self.baa_info["is_active"] = False
            self._save_baa_info()
            return {"status": "expired", "message": f"BAA expired on {expiration.strftime('%Y-%m-%d')}"}
        
        # Check if review is overdue (assuming annual reviews)
        if self.baa_info["last_review_date"]:
            last_review = datetime.fromisoformat(self.baa_info["last_review_date"])
            review_due = last_review + timedelta(days=365)
            
            if now > review_due:
                return {
                    "status": "review_overdue", 
                    "message": f"BAA review is overdue. Last review was on {last_review.strftime('%Y-%m-%d')}"
                }
        
        # BAA is active and valid
        return {
            "status": "active", 
            "message": "BAA is active and valid.",
            "expires_in_days": (expiration - now).days
        }
    
    def add_authorized_personnel(self, username, role, approved_by):
        """Add authorized personnel to the BAA."""
        if not self.baa_info["is_active"]:
            return {"success": False, "message": "Cannot add personnel when BAA is not active"}
        
        # Check if person already exists
        for person in self.baa_info["authorized_personnel"]:
            if person["username"] == username:
                return {"success": False, "message": f"User {username} is already authorized"}
        
        # Add the person
        self.baa_info["authorized_personnel"].append({
            "username": username,
            "role": role,
            "date_added": datetime.now().isoformat(),
            "approved_by": approved_by
        })
        
        # Save changes
        self._save_baa_info()
        
        # Log the action
        self._log_baa_action("add_personnel", f"Added {username} as authorized personnel, approved by {approved_by}")
        
        return {"success": True, "message": f"Added {username} as authorized personnel"}
    
    def remove_authorized_personnel(self, username, reason, removed_by):
        """Remove authorized personnel from the BAA."""
        # Find the person
        found = False
        for i, person in enumerate(self.baa_info["authorized_personnel"]):
            if person["username"] == username:
                # Record removal information
                person["date_removed"] = datetime.now().isoformat()
                person["removal_reason"] = reason
                person["removed_by"] = removed_by
                person["active"] = False
                
                # We don't completely remove them to maintain audit trail
                found = True
                break
        
        if not found:
            return {"success": False, "message": f"User {username} not found in authorized personnel"}
        
        # Save changes
        self._save_baa_info()
        
        # Log the action
        self._log_baa_action("remove_personnel", f"Removed {username} from authorized personnel, removed by {removed_by}, reason: {reason}")
        
        return {"success": True, "message": f"Removed {username} from authorized personnel"}
    
    def is_user_authorized(self, username):
        """Check if a user is authorized under the BAA."""
        if not self.baa_info["is_active"]:
            return False
        
        # Check if user is in authorized personnel
        for person in self.baa_info["authorized_personnel"]:
            if person["username"] == username and person.get("active", True):
                return True
        
        return False
    
    def _log_baa_action(self, action, description):
        """Log BAA-related actions."""
        log_dir = os.path.join(self.baa_dir, "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"baa_log_{datetime.now().strftime('%Y')}.jsonl")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "description": description,
            "user": st.session_state.get("user", {}).get("username", "system")
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")