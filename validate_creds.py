from firebase_admin import credentials
import json

try:
    with open("Musicapi.json", "r") as f:
        data = json.load(f)
    print("✅ JSON is valid")
    print(f"Keys: {list(data.keys())}")
    
    cred = credentials.Certificate("Musicapi.json")
    print("✅ Credentials object created successfully")
except Exception as e:
    print(f"❌ Error: {e}")
