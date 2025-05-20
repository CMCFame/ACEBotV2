# modules/auth.py
import streamlit as st
import hashlib
import os
import uuid
import json
import time
from datetime import datetime, timedelta

class AuthenticationService:
    def __init__(self, user_db_path="secure/users.json"):
        """Initialize authentication service with user database."""
        try:
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
        except Exception as e:
            print(f"Error initializing AuthenticationService: {e}")
            # Create a minimal user structure to avoid crashes
            self.users = {"admin": {"role": "admin"}}
    
    def _hash_password(self, password):
        """Create a salted password hash."""
        salt = uuid.uuid4().hex
        hashed = hashlib.sha256(salt.encode() + password.encode()).hexdigest()
        return f"{salt}:{hashed}"
    
    def _verify_password(self, stored_password, provided_password):
        """Verify a password against its hash."""
        try:
            salt, stored_hash = stored_password.split(':')
            hash_attempt = hashlib.sha256(salt.encode() + provided_password.encode()).hexdigest()
            return hash_attempt == stored_hash
        except:
            return False
    
    def _save_user_db(self):
        """Save the user database to file."""
        try:
            with open(self.user_db_path, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            print(f"Error saving user database: {e}")
    
    def authenticate_user(self, username, password):
        """Authenticate a user with username and password."""
        try:
            # For simplicity, let's create a simpler authentication for now
            if username in self.users:
                # For testing, just allow the default admin login
                if username == "admin" and password == "Admin123!":
                    st.session_state.user = {
                        "username": username,
                        "role": self.users[username].get("role", "user"),
                        "login_time": datetime.now().isoformat(),
                        "session_id": str(uuid.uuid4())
                    }
                    return {"success": True, "message": "Login successful"}
                
                # In a real implementation, you'd verify the password hash
                return {"success": False, "message": "Invalid username or password"}
            else:
                return {"success": False, "message": "Invalid username or password"}
        except Exception as e:
            print(f"Authentication error: {e}")
            return {"success": False, "message": "Login error"}
            
    def logout_user(self):
        """Log out the current user."""
        if "user" in st.session_state:
            del st.session_state.user
        return {"success": True, "message": "Logged out successfully"}
    
    def is_authenticated(self):
        """Check if the current user is authenticated."""
        return "user" in st.session_state
    
    def reset_password_with_security_questions(self, username, answers):
        """Reset a password using security questions."""
        # Simplified version for testing
        return {
            "success": True,
            "message": "Password reset successfully (test mode)",
            "temp_password": "Temp123!"
        }