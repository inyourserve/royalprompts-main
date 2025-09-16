# test_firebase.py
import firebase_admin
from firebase_admin import credentials

try:
    cred = credentials.Certificate('./firebase-service-account.json')
    app = firebase_admin.initialize_app(cred)
    print("✅ Firebase configuration successful!")
    print(f"Project ID: {app.project_id}")
except Exception as e:
    print(f"❌ Firebase configuration failed: {e}")

# made docker hub public
