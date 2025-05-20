# Add new file: modules/auth.py

import streamlit as st
import hashlib
import os
import uuid
import time
from datetime import datetime, timedelta

class AuthenticationService:
    def __init__(self, user_db_path="secure/users.json"):
        """Initialize authentication service with user database."""
        self.user_db_path = user_db_path
        os.makedirs(os.path.dirname(user_db_path), exist_ok=True)
        
        # Load or create user database
        if os.path.exists(user_db_path):
            with open(user_db_path, 'r') as f:
                self.users = json.load(f)
        else:
            self.users = {
                "admin": {
                    "password_hash": self._hash_password("Admin123!"),  # Default admin password
                    "role": "admin",
                    "last_login": None,
                    "created_at": datetime.now().isoformat(),
                    "security_questions": {
                        "What is your mother's maiden name?": self._hash_password("Smith"),
                        "What was your first pet's name?": self._hash_password("Rover")
                    }
                }
            }
            self._save_user_db()
            
        # Initialize login tracking
        if 'login_attempts' not in st.session_state:
            st.session_state.login_attempts = {}
        
    def _hash_password(self, password):
        """Create a salted password hash."""
        salt = uuid.uuid4().hex
        hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        return f"{salt}:{hashed}"
    
    def _verify_password(self, stored_password, provided_password):
        """Verify a password against its hash."""
        salt, stored_hash = stored_password.split(':')
        hash_attempt = hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()
        return hash_attempt == stored_hash
    
    def _save_user_db(self):
        """Save the user database to file."""
        with open(self.user_db_path, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password."""
        # Check for brute force attempts
        ip = self._get_client_ip()
        current_time = time.time()
        
        if ip in st.session_state.login_attempts:
            attempts = st.session_state.login_attempts[ip]
            if len(attempts) >= 5 and (current_time - attempts[0]) < 300:  # 5 attempts within 5 minutes
                return {
                    "success": False, 
                    "message": "Too many login attempts. Please try again later.",
                    "lockout": True
                }
        else:
            st.session_state.login_attempts[ip] = []
        
        # Record this attempt
        st.session_state.login_attempts[ip].append(current_time)
        # Remove old attempts (older than 5 minutes)
        st.session_state.login_attempts[ip] = [t for t in st.session_state.login_attempts[ip] 
                                             if current_time - t < 300]
        
        # Actual authentication
        if username not in self.users:
            return {"success": False, "message": "Invalid username or password"}
            
        user = self.users[username]
        if not self._verify_password(user["password_hash"], password):
            return {"success": False, "message": "Invalid username or password"}
            
        # Update last login time
        self.users[username]["last_login"] = datetime.now().isoformat()
        self._save_user_db()
        
        # Create session
        st.session_state.user = {
            "username": username,
            "role": user["role"],
            "login_time": datetime.now().isoformat(),
            "session_id": str(uuid.uuid4())
        }
        
        # Add to audit log
        self._add_audit_log(username, "login", "User logged in successfully")
        
        return {"success": True, "message": "Login successful", "user": st.session_state.user}
    
    def logout_user(self):
        """Log out the current user."""
        if "user" in st.session_state:
            username = st.session_state.user["username"]
            self._add_audit_log(username, "logout", "User logged out")
            del st.session_state.user
        return {"success": True, "message": "Logged out successfully"}
    
    def change_password(self, username, current_password, new_password):
        """Change a user's password."""
        if username not in self.users:
            return {"success": False, "message": "User not found"}
            
        user = self.users[username]
        if not self._verify_password(user["password_hash"], current_password):
            return {"success": False, "message": "Current password is incorrect"}
            
        # Validate new password
        if not self._is_strong_password(new_password):
            return {"success": False, "message": "Password must be at least 8 characters with upper, lower, digit, and special char"}
            
        # Update password
        self.users[username]["password_hash"] = self._hash_password(new_password)
        self._save_user_db()
        
        # Add to audit log
        self._add_audit_log(username, "change_password", "User changed password")
        
        return {"success": True, "message": "Password changed successfully"}
    
    def _is_strong_password(self, password):
        """Check if a password meets security requirements."""
        if len(password) < 8:
            return False
            
        has_upper = any(c.isupper() for c in password)
        has_lower = any(c.islower() for c in password)
        has_digit = any(c.isdigit() for c in password)
        has_special = any(not c.isalnum() for c in password)
        
        return has_upper and has_lower and has_digit and has_special
    
    def _get_client_ip(self):
        """Get the client's IP address."""
        # This is a simplified version - in production use proper IP extraction
        return "127.0.0.1"
    
    def _add_audit_log(self, username, action, description):
        """Add an entry to the audit log."""
        log_path = "secure/audit_log.jsonl"
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "username": username,
            "action": action,
            "description": description,
            "ip": self._get_client_ip()
        }
        
        with open(log_path, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def is_authenticated(self):
        """Check if the current user is authenticated."""
        if "user" not in st.session_state:
            return False
            
        # Check session expiry (30 minutes)
        login_time = datetime.fromisoformat(st.session_state.user["login_time"])
        if datetime.now() - login_time > timedelta(minutes=30):
            self.logout_user()
            return False
            
        return True
    
    def reset_password_with_security_questions(self, username, answers):
        """Reset a password using security questions."""
        if username not in self.users:
            return {"success": False, "message": "User not found"}
            
        user = self.users[username]
        if "security_questions" not in user:
            return {"success": False, "message": "Security questions not set for this user"}
            
        # Verify all security questions
        for question, answer in answers.items():
            if question not in user["security_questions"]:
                return {"success": False, "message": "Invalid security question"}
                
            if not self._verify_password(user["security_questions"][question], answer):
                return {"success": False, "message": "Incorrect answers to security questions"}
        
        # Generate a secure temporary password
        import random
        import string
        temp_password = ''.join(random.choice(string.ascii_letters + string.digits + "!@#$%^&*") for _ in range(12))
        
        # Update the user's password
        self.users[username]["password_hash"] = self._hash_password(temp_password)
        self.users[username]["password_reset"] = True  # Flag to force password change on next login
        self._save_user_db()
        
        # Add to audit log
        self._add_audit_log(username, "password_reset", "Password reset via security questions")
        
        return {
            "success": True, 
            "message": "Password reset successfully", 
            "temp_password": temp_password
        }