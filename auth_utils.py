from fastapi import HTTPException, Header
import firebase_admin
from firebase_admin import auth
import traceback

# A helper function to verify Firebase ID tokens
async def verify_token(token: str):
    """
    Verify a Firebase token and return the user info.
    
    Args:
        token: The Firebase ID token to verify
        
    Returns:
        User info from the token
        
    Raises:
        HTTPException: If the token is invalid or verification fails
    """
    try:
        # Special case for testing - allow test-token for development
        if token == "Bearer test-token":
            print("Using test token")
            return {"uid": "test-user-123"}
            
        # Extract the token from the Authorization header (remove "Bearer " prefix)
        if token.startswith("Bearer "):
            token = token.split("Bearer ")[1]
            
        # Use Firebase Admin SDK to verify the token
        # This function will raise an exception if the token is invalid
        decoded_token = auth.verify_id_token(token)
        
        # Return the user info from the token
        return {
            "uid": decoded_token.get("uid"),
            "email": decoded_token.get("email"),
            "name": decoded_token.get("name")
        }
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
