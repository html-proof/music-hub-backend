import os
import firebase_admin
from firebase_admin import credentials, auth, firestore
import datetime
import logging

logger = logging.getLogger(__name__)

_initialized = False
_firestore_client = None

# Firebase project config
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "sample-music-65323")
FIREBASE_DATABASE_URL = os.getenv(
    "FIREBASE_DATABASE_URL",
    "https://sample-music-65323-default-rtdb.asia-southeast1.firebasedatabase.app",
)


def initialize_firebase():
    """Initialize Firebase Admin SDK."""
    global _initialized, _firestore_client

    if _initialized:
        return

    cred_path = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase-service-account.json")

    options = {
        "projectId": FIREBASE_PROJECT_ID,
        "databaseURL": FIREBASE_DATABASE_URL,
    }

    try:
        # 1. Try raw JSON from environment variable
        cert_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
        
        # 2. Try Base64 from environment variable
        cert_base64 = os.getenv("FIREBASE_SERVICE_ACCOUNT_BASE64")
        if not cert_json and cert_base64:
            import base64
            try:
                cert_json = base64.b64decode(cert_base64).decode("utf-8")
            except Exception as e:
                print(f"⚠️ Failed to decode FIREBASE_SERVICE_ACCOUNT_BASE64: {e}")

        if cert_json:
            import json
            try:
                cert_dict = json.loads(cert_json)
                cred = credentials.Certificate(cert_dict)
                firebase_admin.initialize_app(cred, options)
                print("✅ Firebase initialized with credentials from environment variable")
            except Exception as e:
                print(f"⚠️ Failed to initialize with environment credentials: {e}")
                # Fall back to file if env fails
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred, options)
                    print(f"✅ Firebase initialized with service account file: {cred_path}")
                else:
                    raise e
        elif os.path.exists(cred_path):
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred, options)
            print(f"✅ Firebase initialized with service account file: {cred_path}")
        else:
            try:
                firebase_admin.initialize_app(options=options)
                print(f"✅ Firebase initialized with project ID: {FIREBASE_PROJECT_ID}")
            except Exception:
                firebase_admin.initialize_app()
                print("✅ Firebase initialized with default credentials")

        _firestore_client = firestore.client()
        _initialized = True
        print(f"✅ Firestore client ready for project: {FIREBASE_PROJECT_ID}")
    except Exception as e:
        print(f"⚠️ Firebase initialization failed: {e}")
        print("⚠️ Running without Firebase - auth will be disabled")
        print("⚠️ To fix: download service account JSON from Firebase Console")
        print(f"⚠️ Place it at: {os.path.abspath(cred_path)}")
        _initialized = False


def get_firestore_client():
    """Get the Firestore client instance."""
    return _firestore_client


def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return full decoded claims."""
    if not _initialized:
        raise Exception("Firebase not initialized")

    decoded = auth.verify_id_token(id_token)
    return decoded


# ============================================================================
# User CRUD — Firestore operations
# ============================================================================

async def get_user(user_id: str) -> dict | None:
    """Get user document from Firestore."""
    db = get_firestore_client()
    if not db:
        return None
    try:
        doc = db.collection("users").document(user_id).get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error getting user {user_id}: {e}")
        return None


async def create_user(
    user_id: str,
    email: str,
    display_name: str = "",
    photo_url: str = "",
    provider: str = "google.com",
) -> dict:
    """Create a new user document in Firestore."""
    db = get_firestore_client()
    if not db:
        return {"uid": user_id, "email": email}

    now = datetime.datetime.now()
    user_data = {
        "uid": user_id,
        "email": email,
        "displayName": display_name,
        "photoUrl": photo_url,
        "provider": provider,
        "createdAt": now,
        "lastLogin": now,
        "onboardingComplete": False,
    }

    try:
        db.collection("users").document(user_id).set(user_data)
        return user_data
    except Exception as e:
        logger.error(f"Error creating user {user_id}: {e}")
        return {"uid": user_id, "email": email}


async def update_last_login(user_id: str):
    """Update user's last login timestamp."""
    db = get_firestore_client()
    if not db:
        return

    try:
        db.collection("users").document(user_id).update({
            "lastLogin": datetime.datetime.now(),
        })
    except Exception as e:
        logger.error(f"Error updating last login for {user_id}: {e}")
