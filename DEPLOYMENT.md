# 🚀 Deployment Guide

## Local Development

```bash
python main.py
# or
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

```bash
# Build and run
docker-compose up -d

# View logs
docker-compose logs -f backend

# Stop
docker-compose down
```

## Railway

1. Push code to GitHub
2. Connect repo to [Railway](https://railway.app)
3. Add environment variables in Railway dashboard:
   - `PORT=8000`
   - `FIREBASE_PROJECT_ID=sample-music-65323`
   - `FIREBASE_CREDENTIALS_PATH=firebase-service-account.json`
4. Upload `firebase-service-account.json` as a volume or use Railway's secret files
5. Deploy — Railway auto-detects the `Dockerfile`

## Google Cloud Run

```bash
# Build
gcloud builds submit --tag gcr.io/sample-music-65323/music-hub-backend

# Deploy
gcloud run deploy music-hub-backend \
  --image gcr.io/sample-music-65323/music-hub-backend \
  --platform managed \
  --region asia-southeast1 \
  --allow-unauthenticated \
  --set-env-vars "FIREBASE_PROJECT_ID=sample-music-65323"
```

> **Note:** On GCP, Firebase Admin SDK auto-detects credentials — no service account file needed.

## Render

1. Connect GitHub repo
2. Set build command: `pip install -r requirements.txt`
3. Set start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add env vars in dashboard

## Environment Variables (all platforms)

| Variable | Required | Description |
|----------|----------|-------------|
| `PORT` | Yes | Server port |
| `FIREBASE_PROJECT_ID` | Yes | Firebase project ID |
| `FIREBASE_CREDENTIALS_PATH` | Yes* | Path to service account JSON |
| `CORS_ORIGINS` | No | Comma-separated origins |

*Not required on GCP (uses default credentials).
