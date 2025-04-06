from fastapi import FastAPI, HTTPException, Header, File, UploadFile
from google.cloud import vision
from auth_utils import verify_token
import os
import base64
import traceback
from typing import Dict, List, Optional
import io

# Initialize Google Cloud Vision client
client = None
try:
    client = vision.ImageAnnotatorClient()
    print("Successfully initialized Google Cloud Vision client")
except Exception as e:
    print(f"Error initializing Google Cloud Vision client: {str(e)}")
    print(traceback.format_exc())
    print(f"GOOGLE_APPLICATION_CREDENTIALS environment variable: {os.environ.get('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')}")

async def analyze_face_emotion(image_content: bytes) -> Dict[str, float]:
    """
    Analyze an image using Google Cloud Vision API to detect emotions
    
    Args:
        image_content: The bytes of the image to analyze
        
    Returns:
        A dictionary of emotions and their confidence scores
    """
    try:
        if not client:
            print("Vision client is not initialized")
            return {"neutral": 1.0}  # Default to neutral if no client
            
        # Create a Vision API image object
        image = vision.Image(content=image_content)
        
        # Print image size for debugging
        print(f"Analyzing image of size: {len(image_content)} bytes")
        
        # Detect faces in the image
        response = client.face_detection(image=image)
        faces = response.face_annotations
        
        if not faces:
            print("No faces detected in the image")
            return {"neutral": 1.0}  # No faces detected, default to neutral
        
        print(f"Detected {len(faces)} faces in the image")
        
        # Get the first face (assuming one person in the image)
        face = faces[0]
        
        # Map likelihood values to scores (VERY_UNLIKELY=0.0, VERY_LIKELY=1.0)
        # Google's likelihood enum: UNKNOWN, VERY_UNLIKELY, UNLIKELY, POSSIBLE, LIKELY, VERY_LIKELY
        likelihood_map = {
            vision.Likelihood.UNKNOWN: 0.0,
            vision.Likelihood.VERY_UNLIKELY: 0.0,
            vision.Likelihood.UNLIKELY: 0.25,
            vision.Likelihood.POSSIBLE: 0.5,
            vision.Likelihood.LIKELY: 0.75,
            vision.Likelihood.VERY_LIKELY: 1.0
        }
        
        # Print raw likelihood values for debugging
        print(f"Raw likelihoods - Joy: {face.joy_likelihood}, Sorrow: {face.sorrow_likelihood}, Anger: {face.anger_likelihood}, Surprise: {face.surprise_likelihood}")
        
        # Extract emotions and their scores
        emotions = {
            "joy": likelihood_map[face.joy_likelihood],
            "sorrow": likelihood_map[face.sorrow_likelihood],
            "anger": likelihood_map[face.anger_likelihood],
            "surprise": likelihood_map[face.surprise_likelihood],
        }
        
        # Add basic neutral emotion with a moderate baseline score
        # This will be overridden if stronger emotions are detected
        emotions["neutral"] = 0.3
        
        print(f"Detected emotions: {emotions}")
        
        # Find the strongest emotion (excluding neutral)
        non_neutral_emotions = {k: v for k, v in emotions.items() if k != "neutral"}
        if non_neutral_emotions:
            max_emotion = max(non_neutral_emotions.items(), key=lambda x: x[1])
            print(f"Strongest emotion: {max_emotion[0]} with score {max_emotion[1]}")
            
            # Lower the threshold to 0.3 - Vision API is often conservative
            if max_emotion[1] >= 0.3:
                # If we have a reasonably confident emotion, reduce the neutral score
                emotions["neutral"] = 0.1
                return emotions
        
        # If no emotion is clearly detected or all are below threshold, 
        # return with neutral as the dominant emotion
        return emotions
    
    except Exception as e:
        print(f"Error analyzing face: {str(e)}")
        print(traceback.format_exc())
        return {"neutral": 1.0}  # Default to neutral on error

# Register emotion detection endpoint in your FastAPI app
# Note: You'll need to add this code to your main.py or create a new API file

# Example of how to add this endpoint to your FastAPI app:
"""
@app.post("/api/detect-emotion")
async def detect_emotion(file: UploadFile = File(...), authorization: str = Header(...)):
    try:
        # Verify the user's token
        user_info = await verify_token(authorization)
        uid = user_info.get("uid")
        
        # Read the image content
        image_content = await file.read()
        
        # Analyze the image for emotions
        emotions = await analyze_face_emotion(image_content)
        
        # Return the detected emotions
        return {"emotions": emotions}
    
    except Exception as e:
        print(f"Error detecting emotion: {str(e)}")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))
""" 