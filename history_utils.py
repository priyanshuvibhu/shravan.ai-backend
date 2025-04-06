# history_utils.py
from firebase_config import db
from firebase_admin import firestore
from typing import List, Dict, Any
import traceback
import datetime

def get_conversation_history(uid: str, limit: int = 8) -> str:
    """
    Retrieve the conversation history for a specific user.
    
    Args:
        uid: The user's unique identifier
        limit: Maximum number of conversation entries to return
        
    Returns:
        A formatted string containing the conversation history
    """
    # Query Firestore for the most recent conversations for this user
    try:
        query = (db.collection("conversations")
                 .where(field_path="uid", op_string="==", value=uid)
                 .order_by("timestamp", direction=firestore.Query.DESCENDING)
                 .limit(limit))

        
        docs = query.stream()  # Use stream() instead of get()
        
        # If no history exists, return empty string
        docs_list = list(docs)
        if len(docs_list) == 0:
            return "No previous conversation history."
        
        # Format the conversation history as a string
        history = []
        for doc in reversed(docs_list):  # Reverse to get chronological order
            data = doc.to_dict()
            history.append(f"You: {data.get('user_message', '')}")
            history.append(f"Bot: {data.get('bot_response', '')}")
        
        return "\n".join(history)
    except Exception as e:
        print(f"Error getting conversation history: {str(e)}")
        print(traceback.format_exc())
        return "Error retrieving conversation history."

def get_user_profile(uid: str) -> str:
    """
    Retrieve or create a user profile with key information about the user.
    /
    Args:
        uid: The user's unique identifier
        
    Returns:
        A formatted string containing user profile information
    """
    try:
        # Try to get the existing user profile
        profile_ref = db.collection("user_profiles").document(uid)
        profile_doc = profile_ref.get()
        
        if profile_doc.exists:
            # Profile exists, format it for the prompt
            profile_data = profile_doc.to_dict()
            profile_sections = []
            
            # Basic information
            if "name" in profile_data:
                profile_sections.append(f"Name: {profile_data['name']}")
            if "age" in profile_data:
                profile_sections.append(f"Age: {profile_data['age']}")
                
            # User preferences
            if "preferences" in profile_data:
                prefs = profile_data["preferences"]
                if prefs:
                    profile_sections.append("Preferences:")
                    for k, v in prefs.items():
                        profile_sections.append(f"- {k}: {v}")
            
            # Health information
            if "health_info" in profile_data:
                health = profile_data["health_info"]
                if health:
                    profile_sections.append("Health Information:")
                    for k, v in health.items():
                        profile_sections.append(f"- {k}: {v}")
            
            # Important people
            if "important_people" in profile_data:
                people = profile_data["important_people"]
                if people:
                    profile_sections.append("Important People:")
                    for person, relation in people.items():
                        profile_sections.append(f"- {person}: {relation}")
            
            # Key facts
            if "key_facts" in profile_data and profile_data["key_facts"]:
                profile_sections.append("Key Facts:")
                for fact in profile_data["key_facts"]:
                    profile_sections.append(f"- {fact}")
            
            if profile_sections:
                return "User Profile:\n" + "\n".join(profile_sections)
            else:
                return "User Profile: Limited information available."
        else:
            # No profile exists yet, create a basic one
            empty_profile = {
                "key_facts": [],
                "preferences": {},
                "health_info": {},
                "important_people": {},
                "mood_history": []
            }
            profile_ref.set(empty_profile)
            return "User Profile: New user, no information available yet."
    except Exception as e:
        print(f"Error getting user profile: {str(e)}")
        print(traceback.format_exc())
        return "Error retrieving user profile."

def update_user_profile(uid: str, message: str, mood: str, bot_response: str) -> None:
    """
    Update the user profile based on the current conversation.
    This function uses basic text analysis to extract information from the conversation
    and update the user's profile accordingly.
    
    Args:
        uid: The user's unique identifier
        message: The user's message
        mood: The user's current mood
        bot_response: The bot's response
    """
    try:
        profile_ref = db.collection("user_profiles").document(uid)
        
        # Create a new mood entry with current timestamp
        new_mood = {
            "mood": mood,
            "timestamp": datetime.datetime.now().isoformat()
        }
        
        # Get the current profile
        profile_doc = profile_ref.get()
        profile_data = {}
        
        if profile_doc.exists:
            profile_data = profile_doc.to_dict()
            # Update mood history
            mood_history = profile_data.get("mood_history", [])
            mood_history.append(new_mood)
            profile_data["mood_history"] = mood_history
        else:
            # Create a new profile with mood_history
            profile_data = {
                "mood_history": [new_mood],
                "key_facts": [],
                "preferences": {},
                "health_info": {},
                "important_people": {}
            }
        
        # Basic information extraction from message
        # Note: A more sophisticated implementation would use proper NLP libraries
        
        # Extract health information
        health_terms = ["diabetes", "blood pressure", "arthritis", "pain", "medication", 
                        "doctor", "hospital", "illness", "disease", "heart", "breathing", 
                        "sleep", "insomnia", "headache", "dizzy", "therapy"]
        health_info = profile_data.get("health_info", {})
        
        for term in health_terms:
            if term in message.lower():
                # Extract sentence containing the health term
                sentences = message.split('.')
                for sentence in sentences:
                    if term in sentence.lower():
                        # Add or update health info
                        health_info[term] = sentence.strip()
        
        # Extract preferences
        preference_patterns = [
            ("like", "likes"),
            ("love", "loves"),
            ("enjoy", "enjoys"),
            ("prefer", "preferences"),
            ("favorite", "favorites"),
            ("hobby", "hobbies")
        ]
        
        preferences = profile_data.get("preferences", {})
        for keyword, category in preference_patterns:
            if keyword in message.lower():
                sentences = message.split('.')
                for sentence in sentences:
                    if keyword in sentence.lower():
                        # Add to preferences
                        preferences[category] = sentence.strip()
        
        # Extract people mentions
        people_indicators = ["my son", "my daughter", "my wife", "my husband", 
                           "my friend", "my neighbor", "my doctor", "my grandchild"]
        
        important_people = profile_data.get("important_people", {})
        for indicator in people_indicators:
            if indicator in message.lower():
                # Try to find a name after the indicator
                idx = message.lower().find(indicator)
                remainder = message[idx + len(indicator):].strip()
                name_end = remainder.find('.')
                if name_end == -1:
                    name_end = len(remainder)
                name_part = remainder[:name_end].strip()
                
                if name_part and len(name_part) < 50:  # Reasonable length for a name + description
                    relationship = indicator.replace("my ", "")
                    important_people[name_part] = relationship
        
        # Extract key facts
        # Look for factual statements or important information
        key_facts = profile_data.get("key_facts", [])
        fact_indicators = ["i am", "i was", "i have been", "i used to", 
                         "my family", "i grew up", "i lived", "i worked"]
        
        for indicator in fact_indicators:
            if indicator in message.lower():
                sentences = message.split('.')
                for sentence in sentences:
                    if indicator in sentence.lower() and len(sentence.strip()) > 10:
                        # Add as a key fact if not already present
                        fact = sentence.strip()
                        if fact not in key_facts and len(key_facts) < 20:  # Limit number of facts
                            key_facts.append(fact)
        
        # Update profile with extracted information
        profile_data.update({
            "health_info": health_info,
            "preferences": preferences,
            "important_people": important_people,
            "key_facts": key_facts
        })
        
        # Save updated profile
        profile_ref.set(profile_data)
        print(f"Updated user profile for {uid} with new information")
        
    except Exception as e:
        print(f"Error updating user profile: {str(e)}")
        print(traceback.format_exc())
