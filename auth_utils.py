from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import auth

# A helper function to verify Firebase ID tokens
async def verify_token(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = authorization.split("Bearer ")[1]
    try:
        # Verify the token using Firebase Admin SDK
        decoded_token = auth.verify_id_token(token)
        return decoded_token  # Contains user information such as 'uid', 'email', etc.
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token verification failed: {e}")
