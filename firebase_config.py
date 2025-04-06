import firebase_admin
from firebase_admin import credentials, firestore

# Replace 'serviceAccountKey.json' with the path to your downloaded JSON credentials
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# Create a Firestore client
db = firestore.client()
