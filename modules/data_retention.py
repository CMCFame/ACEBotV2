# Add new file: modules/data_retention.py

import os
import json
import shutil
from datetime import datetime, timedelta
import streamlit as st

class DataRetentionManager:
    def __init__(self, storage_dir="session_data", retention_days=730):  # 2 years by default
        """Initialize the data retention manager."""
        self.storage_dir = storage_dir
        self.retention_days = retention_days
        self.backup_dir = os.path.join(storage_dir, "backups")
        
        # Ensure directories exist
        os.makedirs(storage_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Archive directory for data that should be retained but not active
        self.archive_dir = os.path.join(storage_dir, "archive")
        os.makedirs(self.archive_dir, exist_ok=True)
    
    def apply_retention_policy(self):
        """
        Apply the retention policy to all data, archiving or purging as needed.
        Returns summary of actions taken.
        """
        now = datetime.now()
        retention_cutoff = now - timedelta(days=self.retention_days)
        
        # Track statistics
        stats = {
            "files_scanned": 0,
            "files_purged": 0,
            "files_archived": 0,
            "errors": 0
        }
        
        # Process main session files
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith(".enc") and not filename.endswith(".json"):
                continue
            
            file_path = os.path.join(self.storage_dir, filename)
            stats["files_scanned"] += 1
            
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # If older than retention period, archive or delete
                if mtime < retention_cutoff:
                    # For HIPAA, we should archive rather than delete immediately
                    archive_path = os.path.join(self.archive_dir, filename)
                    shutil.move(file_path, archive_path)
                    stats["files_archived"] += 1
                    
                    # Log the archival
                    self._log_data_action(filename, "archived", file_path, archive_path)
            except Exception as e:
                stats["errors"] += 1
                self._log_data_action(filename, "error", file_path, None, str(e))
        
        # Process backup files - these can be purged if beyond retention
        for filename in os.listdir(self.backup_dir):
            if not filename.endswith(".enc") and not filename.endswith(".json"):
                continue
            
            file_path = os.path.join(self.backup_dir, filename)
            stats["files_scanned"] += 1
            
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # If older than retention period, purge
                if mtime < retention_cutoff:
                    # Securely delete the file (simple version)
                    self._secure_delete(file_path)
                    stats["files_purged"] += 1
                    
                    # Log the deletion
                    self._log_data_action(filename, "purged", file_path, None)
            except Exception as e:
                stats["errors"] += 1
                self._log_data_action(filename, "error", file_path, None, str(e))
        
        return stats
    
    def _secure_delete(self, file_path):
        """
        Securely delete a file by overwriting with random data before deletion.
        Very basic implementation - in production use specialized secure deletion tools.
        """
        import random
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Overwrite with random data 3 times
        for i in range(3):
            with open(file_path, 'wb') as f:
                f.write(os.urandom(file_size))
                f.flush()
                os.fsync(f.fileno())
        
        # Finally delete the file
        os.remove(file_path)
    
    def _log_data_action(self, filename, action, source_path, dest_path=None, error=None):
        """Log data retention actions to a secure log."""
        log_dir = os.path.join(self.storage_dir, "retention_logs")
        os.makedirs(log_dir, exist_ok=True)
        
        log_file = os.path.join(log_dir, f"retention_{datetime.now().strftime('%Y-%m')}.jsonl")
        
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            "filename": filename,
            "source_path": source_path,
            "destination_path": dest_path,
            "error": error,
            "username": st.session_state.get("user", {}).get("username", "system")
        }
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(log_entry) + "\n")
    
    def archive_completed_sessions(self, completed_only=True):
        """
        Archive sessions that have been completed and are more than 30 days old.
        """
        now = datetime.now()
        archive_cutoff = now - timedelta(days=30)  # Archive after 30 days
        
        # Track statistics
        stats = {"files_scanned": 0, "files_archived": 0, "errors": 0}
        
        # Process session files
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith(".enc") and not filename.endswith(".json"):
                continue
            
            file_path = os.path.join(self.storage_dir, filename)
            stats["files_scanned"] += 1
            
            try:
                # Get file modification time
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                # Skip if not old enough
                if mtime > archive_cutoff:
                    continue
                
                # Check if session is completed (if required)
                if completed_only:
                    is_completed = self._check_session_completed(file_path)
                    if not is_completed:
                        continue
                
                # Archive the session
                archive_path = os.path.join(self.archive_dir, filename)
                shutil.move(file_path, archive_path)
                stats["files_archived"] += 1
                
                # Log the archival
                self._log_data_action(filename, "archived_completed", file_path, archive_path)
            except Exception as e:
                stats["errors"] += 1
                self._log_data_action(filename, "error", file_path, None, str(e))
        
        return stats
    
    # Continuing from where I left off in _check_session_completed method:

    def _check_session_completed(self, file_path):
        """Check if a session file represents a completed questionnaire."""
        # For encrypted files
        if file_path.endswith(".enc"):
            # We would need to decrypt first, which requires the key
            # This is a simplified version that assumes we can't check encrypted files
            return False
        
        try:
            # For JSON files we can check directly
            with open(file_path, 'r') as f:
                session_data = json.load(f)
                
            # Check if explicitly finished or all topics covered
            if session_data.get("explicitly_finished", False):
                return True
                
            # Check if all topics covered
            topic_areas = session_data.get("topic_areas_covered", {})
            if all(topic_areas.values()):
                return True
                
            # If neither condition is met, it's not completed
            return False
        except Exception:
            # If we can't parse the file, assume it's not completed
            return False