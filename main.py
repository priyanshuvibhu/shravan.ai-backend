from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from chatbot import get_enhanced_chatbot_response  # Your enhanced chatbot function using Gemini API
from firebase_config import db  # Import the Firestore client
from firebase_admin import firestore  # Import firestore for SERVER_TIMESTAMP
from auth_utils import verify_token  # Import our token verification function
from fastapi.middleware.cors import CORSMiddleware
from history_utils import get_conversation_history, get_user_profile, update_user_profile  # Import our helper functions
import traceback  # For detailed error reporting

app = FastAPI(title="shravan.ai Backend API")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins - adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data model for the chatbot request
class ChatRequest(BaseModel):
    mood: str
    message: str

# Updated /chat endpoint that includes conversation history and user profile
@app.post("/chat")
async def chat_endpoint(request: ChatRequest, authorization: str = Header(...)):
    try:
        # Verify the user's token
        user_info = await verify_token(authorization)
        uid = user_info.get("uid")
        
        # Retrieve conversation history for context (last 8 messages)
        try:
            history_context = get_conversation_history(uid, limit=8)
            print(f"Successfully retrieved history for user {uid}")
        except Exception as history_error:
            print(f"History error: {str(history_error)}")
            print(traceback.format_exc())
            history_context = "No previous conversation history."
            
        # Retrieve user profile for personalization
        try:
            user_profile = get_user_profile(uid)
            print(f"Successfully retrieved profile for user {uid}")
        except Exception as profile_error:
            print(f"Profile error: {str(profile_error)}")
            print(traceback.format_exc())
            user_profile = "User Profile: No information available."
        
        # Construct a combined prompt including history and profile
        base_prompt = (
            f"CONTEXT (Reference only, do not mention directly):\n"
            f"{user_profile}\n\n"
            f"Previous messages (for context only):\n{history_context}\n\n"
            f"Current user mood: {request.mood}\n"
            f"Current user message: '{request.message}'\n\n"
            "INSTRUCTIONS:\n"
            "You are an AI companion designed to provide emotional support and companionship to elderly users. "
            "Your primary goal is to respond directly to the current message while being empathetic and supportive. "
            
            "CRITICAL REQUIREMENTS (MUST FOLLOW):\n"
            "- DO NOT start messages with 'Hi [Name]' or any similar greeting pattern\n"
            "- DO NOT address the user as his/her name or 'my friend' in every message\n"
            "- DO NOT use the exact same opening in multiple messages\n"
            "- DO NOT mention the user's mood unless directly relevant to your response\n"
            "- VARY your response style significantly between messages\n"
            "- RESPOND DIRECTLY to the content of the message without unnecessary preamble\n"
            
            "Guidelines:\n"
            "1. Focus primarily on the current message without excessive references to previous conversations\n"
            "2. Be concise - keep responses under 3-4 sentences unless the situation requires more detail\n"
            "3. Be conversational and natural, like ChatGPT, not overly formal or clinical\n"
            "4. Respond to emotional needs with empathy, validation, and gentle suggestions when appropriate\n"
            "5. Subtly use profile information to personalize responses WITHOUT explicitly mentioning you have this information\n"
            "6. NEVER use terms like 'beta', 'mom', 'dad', or other familial/parental terms of endearment\n"
            "7. Treat the user with respect as an equal - avoid being condescending or overly simplistic\n"
            
            "Tone: Warm, supportive, respectful, and conversational - similar to ChatGPT but with special attention to elderly users' emotional needs."
        )
        
        try:
            response_text = await get_enhanced_chatbot_response(base_prompt)
            print("Successfully got response from chatbot")
        except Exception as chatbot_error:
            print(f"Chatbot error: {str(chatbot_error)}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error getting chatbot response: {str(chatbot_error)}")
        
        # Prepare conversation data and include the user's unique id (uid)
        conversation = {
            "uid": uid,
            "mood": request.mood,
            "user_message": request.message,
            "bot_response": response_text,
            "timestamp": firestore.SERVER_TIMESTAMP  # Automatically sets the current server time
        }
        
        # Save conversation to Firestore
        try:
            db.collection("conversations").add(conversation)
            print("Successfully saved conversation to Firestore")
            
            # Update user profile based on the conversation
            update_user_profile(uid, request.message, request.mood, response_text)
            print("Successfully updated user profile")
            
        except Exception as db_error:
            print(f"Database error: {str(db_error)}")
            print(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Error saving conversation: {str(db_error)}")
        
        return {"response": response_text}
    except Exception as e:
        print(f"General error: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
def read_root():
    return {"message": "Welcome to shravan.ai Backend!"}
