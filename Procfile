web: sh -c 'if [ -n "$FIREBASE_SERVICE_ACCOUNT_JSON" ]; then echo "$FIREBASE_SERVICE_ACCOUNT_JSON" > firebase-service-account.json; fi && python -m uvicorn main:app --host 0.0.0.0 --port $PORT'
