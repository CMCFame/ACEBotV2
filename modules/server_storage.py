# Create a new file: modules/server_storage.py

import json
import os
import uuid
from datetime import datetime

class ServerStorage:
    def __init__(self, storage_dir="session_data"):
        # Create storage directory if it doesn't exist
        os.makedirs(storage_dir, exist_ok=True)
        self.storage_dir = storage_dir
        
    def save_session(self, session_data):
        # Generate a unique session ID if not present
        if "session_id" not in session_data:
            session_data["session_id"] = str(uuid.uuid4())
        
        # Add timestamp
        session_data["last_saved"] = datetime.now().isoformat()
        
        # Save to file
        session_id = session_data["session_id"]
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        
        with open(file_path, 'w') as f:
            json.dump(session_data, f)
            
        return {
            "success": True,
            "session_id": session_id,
            "file_path": file_path,
            "message": f"Session saved to server with ID: {session_id}"
        }
    
    def load_session(self, session_id):
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"Session with ID {session_id} not found"
            }
            
        try:
            with open(file_path, 'r') as f:
                session_data = json.load(f)
                
            return {
                "success": True,
                "session_data": session_data,
                "message": f"Session {session_id} loaded successfully"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error loading session: {str(e)}"
            }