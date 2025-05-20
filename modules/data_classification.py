# Add new file: modules/data_classification.py

import re
import json
import streamlit as st

class PHIDataClassifier:
    def __init__(self):
        """Initialize the PHI data classifier."""
        # Load PHI patterns for detection
        self.phi_patterns = {
            "name": r'\b[A-Z][a-z]+ [A-Z][a-z]+\b',
            "ssn": r'\b\d{3}[-\s]?\d{2}[-\s]?\d{4}\b',
            "phone": r'\b(\+\d{1,2}\s)?\(?\d{3}\)?[\s.-]?\d{3}[\s.-]?\d{4}\b',
            "email": r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b',
            "address": r'\b\d+\s+[A-Za-z0-9\s,]+(?:Street|St|Avenue|Ave|Road|Rd|Highway|Hwy|Square|Sq|Trail|Trl|Drive|Dr|Court|Ct|Park|Parkway|Pkwy|Circle|Cir|Boulevard|Blvd)\b',
            "medical_record": r'\bMR[0-9]{6,}\b|\b[0-9]{6,}MR\b',
            "date_of_birth": r'\b(0?[1-9]|1[0-2])[\/\-](0?[1-9]|[12]\d|3[01])[\/\-](19|20)\d{2}\b',
            "health_plan_beneficiary": r'\b[A-Z]{3}[0-9]{9,11}\b',
            "account_number": r'\b[A-Z0-9]{8,12}\b',
            "certificate_license": r'\b[A-Z]{2,5}\-[0-9]{5,10}\b',
            "vehicle_identifier": r'\b[A-Z0-9]{17}\b',
            "device_identifier": r'\b[A-Z0-9\-]{8,16}\b',
            "biometric_identifier": r'\b[A-Z0-9]{16,24}\b',
            "photo_identifier": r'\bPHOTO[A-Z0-9]{8,12}\b',
            "geographic_subdivision": r'\b[A-Z]{2}\s[0-9]{5}(?:\-[0-9]{4})?\b'
        }
    
    def scan_text_for_phi(self, text):
        """Scan text for potential PHI markers."""
        if not text:
            return {"has_phi": False, "phi_types": []}
        
        found_phi = {}
        
        for phi_type, pattern in self.phi_patterns.items():
            matches = re.findall(pattern, text)
            if matches:
                found_phi[phi_type] = len(matches)
        
        return {"has_phi": bool(found_phi), "phi_types": found_phi}
    
    def redact_phi(self, text):
        """Redact potential PHI from text."""
        if not text:
            return text
        
        redacted_text = text
        
        for phi_type, pattern in self.phi_patterns.items():
            replacement = f"[REDACTED {phi_type.upper()}]"
            redacted_text = re.sub(pattern, replacement, redacted_text)
        
        return redacted_text
    
    def classify_session_data(self, session_data):
        """Classify an entire session for PHI content."""
        # Track PHI throughout the session
        phi_summary = {
            "contains_phi": False,
            "phi_locations": [],
            "phi_types_found": set()
        }
        
        # Check user info
        if "user_info" in session_data:
            user_info = session_data["user_info"]
            if user_info.get("name") or user_info.get("company"):
                user_text = f"{user_info.get('name', '')} {user_info.get('company', '')}"
                phi_result = self.scan_text_for_phi(user_text)
                
                if phi_result["has_phi"]:
                    phi_summary["contains_phi"] = True
                    phi_summary["phi_locations"].append("user_info")
                    for phi_type in phi_result["phi_types"]:
                        phi_summary["phi_types_found"].add(phi_type)
        
        # Check responses
        if "responses" in session_data:
            for i, (question, answer) in enumerate(session_data["responses"]):
                phi_result = self.scan_text_for_phi(answer)
                
                if phi_result["has_phi"]:
                    phi_summary["contains_phi"] = True
                    phi_summary["phi_locations"].append(f"response_{i}")
                    for phi_type in phi_result["phi_types"]:
                        phi_summary["phi_types_found"].add(phi_type)
        
        # Check chat history
        if "chat_history" in session_data:
            for i, message in enumerate(session_data["chat_history"]):
                if message.get("role") == "user":
                    phi_result = self.scan_text_for_phi(message.get("content", ""))
                    
                    if phi_result["has_phi"]:
                        phi_summary["contains_phi"] = True
                        phi_summary["phi_locations"].append(f"chat_history_{i}")
                        for phi_type in phi_result["phi_types"]:
                            phi_summary["phi_types_found"].add(phi_type)
        
        # Convert set to list for JSON serialization
        phi_summary["phi_types_found"] = list(phi_summary["phi_types_found"])
        
        return phi_summary
    
    def create_redacted_session(self, session_data):
        """Create a redacted copy of session data with PHI removed."""
        # Create a deep copy to avoid modifying the original
        import copy
        redacted_data = copy.deepcopy(session_data)
        
        # Redact user info
        if "user_info" in redacted_data:
            redacted_data["user_info"]["name"] = self.redact_phi(redacted_data["user_info"].get("name", ""))
            redacted_data["user_info"]["company"] = self.redact_phi(redacted_data["user_info"].get("company", ""))
        
        # Redact responses
        if "responses" in redacted_data:
            for i, (question, answer) in enumerate(redacted_data["responses"]):
                redacted_data["responses"][i] = (question, self.redact_phi(answer))
        
        # Redact chat history
        if "chat_history" in redacted_data:
            for i, message in enumerate(redacted_data["chat_history"]):
                if message.get("role") == "user":
                    redacted_data["chat_history"][i]["content"] = self.redact_phi(message.get("content", ""))
        
        # Add redaction metadata
        redacted_data["_redacted"] = {
            "timestamp": datetime.now().isoformat(),
            "redacted_by": st.session_state.get("user", {}).get("username", "system"),
            "reason": "PHI protection"
        }
        
        return redacted_data