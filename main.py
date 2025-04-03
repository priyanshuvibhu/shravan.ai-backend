# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from chatbot import get_enhanced_chatbot_response  # Updated function using Gemini API

app = FastAPI(title="shravan.ai Backend API")

# Data model for the chatbot request
class ChatRequest(BaseModel):
    mood: str
    message: str

# Updated /chat endpoint using the enhanced chatbot logic with Gemini API
@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        # Call the enhanced function asynchronously
        response_text = await get_enhanced_chatbot_response(request.mood, request.message)
    except Exception as e:
        # Raise an HTTPException if there's an error with the API call
        raise HTTPException(status_code=500, detail=str(e))
    return {"response": response_text}

@app.get("/")
def read_root():
    return {"message": "Welcome to shravan.ai Backend!"}
