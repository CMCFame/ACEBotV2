# utils/helpers.py
import streamlit as st
import os
import json

def load_instructions(file_path):
    """Load the system instructions from a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        st.error(f"Error loading instructions: {e}")
        return "Error loading instructions. Please check the file path and permissions."

def load_questions(file_path):
    """Load the questions list from a file."""
    try:
        with open(file_path, 'r') as file:
            # Skip question numbers and just store the actual questions
            questions = []
            for line in file:
                line = line.strip()
                if line:
                    # Remove the number and period at the beginning of the line
                    # Assuming format like "1. Question text"
                    parts = line.split('. ', 1)
                    if len(parts) > 1:
                        questions.append(parts[1])
                    else:
                        questions.append(line)  # No number found, add the whole line
            return questions
    except Exception as e:
        st.error(f"Error loading questions: {e}")
        return ["Error loading questions. Please check the file path and permissions."]

def load_css(file_path):
    """Load CSS styles from a file."""
    try:
        with open(file_path, 'r') as file:
            return file.read()
    except Exception as e:
        print(f"Error loading CSS: {e}")
        # Return default CSS if file not found
        return """
        body {
            font-family: sans-serif;
        }
        """

def apply_css(css_content):
    """Apply CSS to the Streamlit app."""
    st.markdown(f'<style>{css_content}</style>', unsafe_allow_html=True)