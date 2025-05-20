# modules/server_storage.py

import json
import os
import uuid
from datetime import datetime
import time

class ServerStorage:
    def __init__(self, storage_dir="session_data"):
        """Initialize server storage with improved error handling and backup mechanisms."""
        # Create storage directory if it doesn't exist
        try:
            os.makedirs(storage_dir, exist_ok=True)
            # Create a backup directory for automatic backups
            os.makedirs(os.path.join(storage_dir, "backups"), exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create storage directories: {e}")
            
        self.storage_dir = storage_dir
        self.backup_dir = os.path.join(storage_dir, "backups")
        
    def save_session(self, session_data):
        """
        Save session data to server with improved error handling and backups.
        
        Args:
            session_data: Dictionary containing session state
            
        Returns:
            dict: Result of the operation with session_id
        """
        try:
            # Generate a unique session ID if not present or preserve existing one
            if "session_id" not in session_data:
                session_data["session_id"] = str(uuid.uuid4())
            
            # Add timestamp
            session_data["last_saved"] = datetime.now().isoformat()
            
            # Save to file
            session_id = session_data["session_id"]
            file_path = os.path.join(self.storage_dir, f"{session_id}.json")
            
            # If file exists, create a backup first
            if os.path.exists(file_path):
                self._create_backup(session_id)
            
            with open(file_path, 'w') as f:
                json.dump(session_data, f, indent=2)
                
            return {
                "success": True,
                "session_id": session_id,
                "file_path": file_path,
                "message": f"Session saved to server with ID: {session_id}"
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error saving session: {str(e)}"
            }
    
    def load_session(self, session_id):
        """
        Load session data from server with improved error handling and fallback to backups.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            dict: Result of the operation with session_data if successful
        """
        file_path = os.path.join(self.storage_dir, f"{session_id}.json")
        
        try:
            # First try to load the main file
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    session_data = json.load(f)
                    
                return {
                    "success": True,
                    "session_data": session_data,
                    "message": f"Session {session_id} loaded successfully"
                }
            
            # If main file doesn't exist, try to find a backup
            backup_file = self._find_latest_backup(session_id)
            if backup_file:
                with open(backup_file, 'r') as f:
                    session_data = json.load(f)
                
                return {
                    "success": True,
                    "session_data": session_data,
                    "message": f"Session {session_id} loaded from backup"
                }
            
            # No backup found
            return {
                "success": False,
                "message": f"Session with ID {session_id} not found"
            }
            
        except json.JSONDecodeError:
            # JSON parsing error - try backup
            backup_file = self._find_latest_backup(session_id)
            if backup_file:
                try:
                    with open(backup_file, 'r') as f:
                        session_data = json.load(f)
                    
                    return {
                        "success": True,
                        "session_data": session_data,
                        "message": f"Main session file corrupted. Loaded from backup."
                    }
                except Exception as e:
                    return {
                        "success": False,
                        "message": f"Both main file and backup are corrupted: {str(e)}"
                    }
            else:
                return {
                    "success": False,
                    "message": f"Session file is corrupted and no backup found"
                }
        except Exception as e:
            return {
                "success": False,
                "message": f"Error loading session: {str(e)}"
            }
    
    def _create_backup(self, session_id):
        """Create a backup of the session file before overwriting."""
        try:
            source_path = os.path.join(self.storage_dir, f"{session_id}.json")
            if not os.path.exists(source_path):
                return False
                
            # Create timestamp for unique backup filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"{session_id}_{timestamp}.json")
            
            # Copy file content
            with open(source_path, 'r') as source:
                content = source.read()
                
            with open(backup_path, 'w') as backup:
                backup.write(content)
                
            return True
        except Exception as e:
            print(f"Warning: Failed to create backup: {e}")
            return False
    
    def _find_latest_backup(self, session_id):
        """Find the most recent backup for a session."""
        try:
            # Get all backup files for this session
            backup_files = [f for f in os.listdir(self.backup_dir) 
                           if f.startswith(session_id) and f.endswith('.json')]
            
            if not backup_files:
                return None
                
            # Sort by timestamp (which is part of the filename)
            backup_files.sort(reverse=True)
            
            # Return the most recent backup
            return os.path.join(self.backup_dir, backup_files[0])
        except Exception as e:
            print(f"Warning: Error finding backup files: {e}")
            return None
            
    def list_sessions(self, limit=10):
        """
        List available sessions with basic information.
        
        Args:
            limit: Maximum number of sessions to return (most recent first)
            
        Returns:
            list: List of session info dictionaries
        """
        try:
            # Get all session files
            session_files = [f for f in os.listdir(self.storage_dir) 
                            if f.endswith('.json') and os.path.isfile(os.path.join(self.storage_dir, f))]
            
            sessions = []
            
            for filename in session_files:
                try:
                    # Extract session ID from filename
                    session_id = filename.replace('.json', '')
                    
                    # Get file metadata
                    file_path = os.path.join(self.storage_dir, filename)
                    modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # Get basic session info
                    with open(file_path, 'r') as f:
                        session_data = json.load(f)
                        
                    sessions.append({
                        "session_id": session_id,
                        "last_saved": session_data.get("last_saved", modified_time.isoformat()),
                        "user_name": session_data.get("user_info", {}).get("name", "Unknown"),
                        "company": session_data.get("user_info", {}).get("company", "Unknown"),
                        "progress": self._calculate_progress(session_data)
                    })
                except Exception as e:
                    # Skip problematic files
                    print(f"Warning: Error processing session file {filename}: {e}")
                    continue
            
            # Sort by last saved time (most recent first)
            sessions.sort(key=lambda x: x["last_saved"], reverse=True)
            
            # Return limited number
            return sessions[:limit]
            
        except Exception as e:
            print(f"Error listing sessions: {e}")
            return []
    
    def _calculate_progress(self, session_data):
        """Calculate completion progress as a percentage."""
        try:
            # Check if we have topic tracking
            if "topic_areas_covered" in session_data:
                covered = sum(1 for v in session_data["topic_areas_covered"].values() if v)
                total = len(session_data["topic_areas_covered"])
                if total > 0:
                    return int((covered / total) * 100)
            
            # Fallback to question index
            if "current_question_index" in session_data and session_data.get("questions_count", 0) > 0:
                return int((session_data["current_question_index"] / session_data["questions_count"]) * 100)
                
            # Can't determine progress
            return 0
        except Exception:
            return 0
            
# modules/server_storage.py - Add methods for encrypted data

def save_encrypted_session(self, encrypted_data):
    """
    Save encrypted session data to server.
    
    Args:
        encrypted_data: Encrypted binary data
        
    Returns:
        dict: Result of the operation with session_id
    """
    try:
        # Generate a unique session ID if not present
        session_id = str(uuid.uuid4())
        
        # Save to file
        file_path = os.path.join(self.storage_dir, f"{session_id}.enc")
        
        with open(file_path, 'wb') as f:
            f.write(encrypted_data)
            
        return {
            "success": True,
            "session_id": session_id,
            "file_path": file_path,
            "message": f"Encrypted session saved to server with ID: {session_id}"
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Error saving encrypted session: {str(e)}"
        }

def load_encrypted_session(self, session_id):
    """
    Load encrypted session data from server.
    
    Args:
        session_id: ID of the session to load
        
    Returns:
        dict: Result of the operation with encrypted_data if successful
    """
    file_path = os.path.join(self.storage_dir, f"{session_id}.enc")
    
    try:
        # Check if file exists
        if not os.path.exists(file_path):
            return {
                "success": False,
                "message": f"Session with ID {session_id} not found"
            }
            
        # Read the encrypted data
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
            
        return {
            "success": True,
            "encrypted_data": encrypted_data,
            "message": f"Encrypted session {session_id} loaded successfully"
        }
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Error loading encrypted session: {str(e)}"
        }