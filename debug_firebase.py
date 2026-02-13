from services.firebase_db import _ref
from config.firebase_init import initialize_firebase
import logging

logging.basicConfig(level=logging.INFO)

initialize_firebase()

try:
    print("Attempting to get /auto_playlists/test_id")
    data = _ref("/auto_playlists/test_id").get()
    print(f"Result: {data}")
except Exception as e:
    print(f"Error: {e}")
