# config.py
import os

# OpenAI API Configuration (can be kept for reference or other uses)
OPENAI_MODEL = "gpt-4o-2024-08-06"

# Amazon Bedrock Configuration
BEDROCK_MODEL_ID = "us.anthropic.claude-3-7-sonnet-20250219-v1:0" # Claude 3.5 Sonnet model ID
BEDROCK_AWS_REGION = "us-east-2" # Or your preferred AWS region for Bedrock

DEFAULT_MAX_TOKENS = 1024 # Adjusted for Claude, can be tuned
DEFAULT_TEMPERATURE = 0.7

# Cookie Management
COOKIE_PREFIX = "ace_"
COOKIE_PASSWORD_ENV = "COOKIES_PASSWORD"
COOKIE_DEFAULT_PASSWORD = "Awm9X0RUnU"  # Only used if env var not set
COOKIE_KEYS = {
    "SESSION": "session_data",
    "TEST": "test_cookie"
}

# File Paths
PROMPT_FILE = "data/prompts/system_prompt.txt" #
QUESTIONS_FILE = "data/questions.txt" #
CSS_FILE = "assets/style.css" #

# Email Configuration
EMAIL_CONFIG = {
    "SENDER_KEY": "EMAIL_SENDER",
    "PASSWORD_KEY": "EMAIL_PASSWORD",
    "RECIPIENT_KEY": "EMAIL_RECIPIENT",
    "SMTP_SERVER_KEY": "SMTP_SERVER",
    "SMTP_PORT_KEY": "SMTP_PORT",
    "DEFAULT_SMTP_SERVER": "smtp.gmail.com",
    "DEFAULT_SMTP_PORT": 587
}

# Topic Areas - Dictionary with display names for UI
TOPIC_AREAS = {
    "basic_info": "Basic Information",
    "staffing_details": "Staffing Details",
    "contact_process": "Contact Process",
    "list_management": "List Management",
    "insufficient_staffing": "Insufficient Staffing",
    "calling_logistics": "Calling Logistics",
    "list_changes": "List Changes",
    "tiebreakers": "Tiebreakers",
    "additional_rules": "Additional Rules"
} #

# Critical questions that must be asked for each topic
CRITICAL_QUESTIONS = {
    "contact_process": [
        "who do you call first",
        "why do you call this person first",
        "how many devices do employees have",
        "which device is called first and why"
    ],
    "list_management": [
        "are lists based on attributes other than job classification",
        "how exactly do you call the list",
        "do you skip around on lists based on qualifications or status",
        "are there pauses between calls"
    ],
    "insufficient_staffing": [
        "do you offer positions to people not normally called",
        "do you consider or call the whole list again",
        "do you always follow these procedures the same way",
        "are there situations where you handle this differently"
    ],
    "additional_rules": [
        "are there rules that excuse declined callouts near shifts or vacations"
    ]
} #