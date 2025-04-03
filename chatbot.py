import httpx
from fastapi import HTTPException

async def query_gemini_api(prompt: str) -> str:
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key=AIzaSyCQs0oGDvKE8FzD0nxbkq4qLVVVtI_JuB8"
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "contents": [{
            "parts": [{
                "text": prompt
            }]
        }]
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=f"Gemini API error: {response.text}")
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError):
            return "I'm here for you, always."

async def get_enhanced_chatbot_response(mood: str, user_message: str) -> str:
    base_response = (
        f"Based on your mood ({mood}), you said: '{user_message}'. "
        "Now, please interact like a caring son who genuinely cares about you. "
        "Make the response short and simple thinking as the user as an old person. "
        "Keep the language warm, personal, and supportive, like a loving son would speak to his parent."
        "Don't address the user with mother or father and do remember you are a mental health chatbot."
    )
    enhanced_response = await query_gemini_api(base_response)
    return enhanced_response
