# modules/topic_tracker.py
import streamlit as st
import json
import re
from config import TOPIC_AREAS, CRITICAL_QUESTIONS

class TopicTracker:
    def __init__(self):
        """Initialize the topic tracker with the predefined topic areas."""
        # Initialize if not already in session state
        if 'topic_areas_covered' not in st.session_state:
            st.session_state.topic_areas_covered = {topic: False for topic in TOPIC_AREAS.keys()}
    
    def process_topic_update(self, message_content):
        """
        Process topic update messages from the AI.
        Returns True if the message was a topic update, False otherwise.
        """
        if "TOPIC_UPDATE:" not in message_content:
            return False
            
        try:
            # Extract the JSON part after TOPIC_UPDATE:
            json_str = message_content.split("TOPIC_UPDATE:")[1].strip()
            # Sometimes the AI might add additional text after the JSON
            json_str = json_str.split("\n")[0].strip()
            
            # Log the extracted string for debugging
            print(f"Extracted JSON string: {json_str}")
            
            topic_updates = json.loads(json_str)
            
            # Update the session state
            for topic, status in topic_updates.items():
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = status
                    print(f"Updated topic {topic} to {status}")
            
            # After updating topics, check for completion
            self._check_completion_status()
            
            # Check for missing critical questions
            self._check_critical_questions()
            
            return True
        except Exception as e:
            print(f"Error processing topic update: {e}")
            # If there's an error, still return True to avoid displaying the message
            return True
    
    def _check_completion_status(self):
        """Check if all topics are covered and trigger appropriate actions."""
        # Count covered topics
        covered_count = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        
        # If we're near completion (7+ topics covered), check for missing topics
        if covered_count >= 7:
            missing_topics = [t for t, v in st.session_state.topic_areas_covered.items() if not v]
            if missing_topics:
                # Add system message to explicitly ask about missing topics
                missing_topics_str = ", ".join([TOPIC_AREAS[t] for t in missing_topics])
                st.session_state.chat_history.append({
                    "role": "system",
                    "content": f"IMPORTANT: The following topics have not been covered yet: {missing_topics_str}. Focus your next questions specifically on these topics until all are covered."
                })
                print(f"Added system message about missing topics: {missing_topics_str}")
    
    def _check_critical_questions(self):
        """Check if critical questions for covered topics have been asked."""
        # Get all conversation text
        conversation_text = " ".join([
            msg.get("content", "") for msg in st.session_state.chat_history 
            if isinstance(msg, dict) and msg.get("role") in ["assistant", "user"]
        ]).lower()
        
        # Check each covered topic for its critical questions
        for topic, is_covered in st.session_state.topic_areas_covered.items():
            if is_covered and topic in CRITICAL_QUESTIONS:
                missing_questions = []
                
                for question in CRITICAL_QUESTIONS[topic]:
                    # Check if this critical question has been asked
                    if question.lower() not in conversation_text:
                        missing_questions.append(question)
                
                if missing_questions:
                    # Add a system message to ask these questions
                    question_str = ", ".join(missing_questions)
                    st.session_state.chat_history.append({
                        "role": "system",
                        "content": f"IMPORTANT: Although the {TOPIC_AREAS[topic]} topic is marked as covered, you have not specifically asked about: {question_str}. Please ask about these points before moving to other topics."
                    })
    
    def check_summary_readiness(self):
        """
        Check if the questionnaire is ready for summary generation.
        Returns dict with readiness status and any missing topics/questions.
        """
        # Check if all topics are covered
        all_topics_covered = all(st.session_state.topic_areas_covered.values())
        
        if not all_topics_covered:
            missing_topics = [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
            return {
                "ready": False,
                "missing_topics": missing_topics,
                "message": f"The following topics still need to be covered: {', '.join(missing_topics)}"
            }
        
        # Get answered questions count
        from modules.summary import SummaryGenerator
        summary_gen = SummaryGenerator()
        responses = summary_gen.get_responses_as_list()
        
        # Check if at least 70% of questions have been answered
        answered_count = len(responses)
        total_questions = len(st.session_state.questions)
        
        if answered_count / total_questions < 0.7:
            missing_count = total_questions - answered_count
            return {
                "ready": False,
                "missing_questions": [f"{missing_count} questions still unanswered"],
                "message": f"Please continue answering questions. There are still approximately {missing_count} questions that need answers."
            }
        
        # All topics have sufficient coverage
        return {
            "ready": True,
            "message": "All topics and critical questions have been covered. Ready for summary."
        }
    
    def get_progress_percentage(self):
        """Calculate the current progress percentage based on topic coverage."""
        covered_topics = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        return int((covered_topics / total_topics) * 100)
    
    def get_progress_data(self):
        """Get detailed progress data for UI display."""
        covered_topics = sum(st.session_state.topic_areas_covered.values())
        total_topics = len(st.session_state.topic_areas_covered)
        
        return {
            "percentage": int((covered_topics / total_topics) * 100),
            "covered_count": covered_topics,
            "total_count": total_topics,
            "covered_topics": [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if v],
            "missing_topics": [TOPIC_AREAS[t] for t, v in st.session_state.topic_areas_covered.items() if not v]
        }
    
    def create_progress_dashboard_artifact(self):
        """Create a React artifact for the progress dashboard."""
        # Get current progress data
        progress_data = self.get_progress_data()
        
        # Create a simplified version of question coverage
        question_coverage = {}
        for topic in TOPIC_AREAS.keys():
            if topic in st.session_state.topic_areas_covered and st.session_state.topic_areas_covered[topic]:
                question_coverage[topic] = {
                    "covered": 1,
                    "total": 1,
                    "percentage": 100
                }
            else:
                question_coverage[topic] = {
                    "covered": 0,
                    "total": 1,
                    "percentage": 0
                }
        
        # Serialize the data for the React component
        progress_json = json.dumps({
            "overall": progress_data,
            "topicDetails": question_coverage
        })
        
        # Generate the React component
        artifact_content = f"""
import React from 'react';

const ProgressDashboard = () => {{
  // Load progress data
  const progressData = {progress_json};
  const overall = progressData.overall;
  const topicDetails = progressData.topicDetails;
  
  // Format percentage
  const formatPct = (pct) => `${{pct}}%`;
  
  return (
    <div className="p-4 bg-white rounded-lg shadow">
      <h2 className="text-xl font-bold mb-4 text-center">ACE Questionnaire Progress</h2>
      
      {/* Overall progress */}
      <div className="mb-4 p-3 bg-gray-100 rounded">
        <div className="flex justify-between items-center mb-2">
          <span className="text-gray-700 font-medium">Overall Completion</span>
          <span className="font-bold">{{formatPct(overall.percentage)}}</span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-4 overflow-hidden">
          <div 
            className="h-4 rounded-full bg-blue-500"
            style={{{{width: `${{overall.percentage}}%`}}}}
          ></div>
        </div>
        <div className="text-center mt-2 text-sm text-gray-600">
          {{overall.covered_count}} of {{overall.total_count}} topic areas covered
        </div>
      </div>
      
      {/* Topic coverage list */}
      <div className="mb-4">
        <h3 className="text-lg font-semibold mb-2">Topic Area Coverage</h3>
        <div className="grid gap-3">
          {{Object.entries(topicDetails).map(([topic, details]) => (
            <div key={{topic}} className="p-2 border-b border-gray-200">
              <div className="flex justify-between items-center mb-1">
                <span className="font-medium">{{topic.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')}}</span>
                <span className="text-sm font-semibold">
                  {{details.percentage < 100 ? 
                    <span className="text-orange-500">In Progress</span> : 
                    <span className="text-green-500">✓ Complete</span>}}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2 overflow-hidden">
                <div 
                  className={{`h-2 rounded-full ${{details.percentage < 100 ? 'bg-orange-400' : 'bg-green-500'}}`}}
                  style={{{{width: `${{details.percentage}}%`}}}}
                ></div>
              </div>
            </div>
          ))}}
        </div>
      </div>
      
      {/* Topic status */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="p-3 bg-green-50 rounded border border-green-200">
          <h3 className="text-base font-semibold mb-2 text-green-700">✓ Covered Topics</h3>
          <ul className="list-disc pl-5 text-sm text-green-800 space-y-1">
            {{overall.covered_topics.length > 0 ?
              overall.covered_topics.map(topic => (
                <li key={{topic}}>{{topic}}</li>
              )) :
              <li>No topics fully covered yet</li>
            }}
          </ul>
        </div>
        
        <div className="p-3 bg-yellow-50 rounded border border-yellow-200">
          <h3 className="text-base font-semibold mb-2 text-yellow-700">⏳ Still Needed</h3>
          <ul className="list-disc pl-5 text-sm text-yellow-800 space-y-1">
            {{overall.missing_topics.length > 0 ?
              overall.missing_topics.map(topic => (
                <li key={{topic}}>{{topic}}</li>
              )) :
              <li>All topic areas covered!</li>
            }}
          </ul>
        </div>
      </div>
      
      <div className="text-center mt-4 text-xs text-gray-500">
        Last updated: {{new Date().toLocaleString()}}
      </div>
    </div>
  );
}};

export default ProgressDashboard;
"""
        
        # Return the artifact definition
        return {
            "command": "create",
            "id": "progress-dashboard",
            "type": "application/vnd.ant.react",
            "title": "Progress Dashboard",
            "content": artifact_content
        }
    
    def update_ai_context_after_answer(self, user_input):
        """Update AI context after each user answer to prevent circular questioning."""
        # Analyze the last few messages to determine what question was just answered
        if len(st.session_state.visible_messages) >= 2:
            last_msg = st.session_state.visible_messages[-1]  # User's answer
            prev_msg = st.session_state.visible_messages[-2]  # Assistant's question
            
            if last_msg["role"] == "user" and prev_msg["role"] == "assistant":
                # Check if this is a substantive answer (not just asking for an example)
                if last_msg["content"].lower().strip() not in ["example", "can you show me an example?", "show example"]:
                    # Extract the question from the assistant's message
                    question_asked = ""
                    for sentence in prev_msg["content"].split(". "):
                        if "?" in sentence:
                            question_asked = sentence.strip() + "?"
                            break
                    
                    if question_asked:
                        # Check which of our original questions this might be
                        matched_questions = []
                        for i, q in enumerate(st.session_state.questions):
                            # Simple word overlap check
                            q_words = set(q.lower().split())
                            asked_words = set(question_asked.lower().split())
                            overlap = q_words.intersection(asked_words)
                            if len(overlap) > 0 and len(overlap) / max(len(q_words), 1) > 0.3:
                                matched_questions.append(i)
                        
                        # Add context message to avoid asking this question again
                        if matched_questions:
                            question_info = ", ".join([f"question {i+1}" for i in matched_questions])
                            context_msg = {
                                "role": "system",
                                "content": f"The user has just answered {question_info} with: '{last_msg['content']}'. Do not ask this question again."
                            }
                            st.session_state.chat_history.append(context_msg)
                            
                            # Also check if this completes a topic
                            self._update_topic_coverage_from_answer(question_asked, last_msg["content"])
    
    def _update_topic_coverage_from_answer(self, question, answer):
        """Update topic coverage based on answers to key questions."""
        combined_text = (question + " " + answer).lower()
        
        # Map of key phrases to topics they complete
        completion_phrases = {
            "contact first": "contact_process",
            "devices have": "contact_process", 
            "call straight down": "list_management",
            "skip those who are on": "list_management",
            "call neighboring district": "insufficient_staffing",
            "call all devices simultaneously": "calling_logistics",
            "lists update": "list_changes",
            "seniority is used as": "tiebreakers",
            "hours of rest": "additional_rules"
        }
        
        # Check for completion phrases
        for phrase, topic in completion_phrases.items():
            if phrase in combined_text:
                if topic in st.session_state.topic_areas_covered:
                    st.session_state.topic_areas_covered[topic] = True