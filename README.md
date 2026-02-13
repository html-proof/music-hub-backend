# 🎵 Music Hub Backend

Production-ready **FastAPI + Firebase** backend for a Spotify-like music streaming app. Uses **yt-dlp** for YouTube audio extraction with aggressive caching for <5 second playback.

## ⚡ Performance

| Operation | Latency |
|-----------|---------|
| Cached stream URL | <50ms |
| Fresh URL resolve | <2s |
| Search | <500ms |
| Cache hit rate | 80%+ |

## 🚀 Quick Start

```bash
# 1. Setup
bash setup.sh

# 2. Add Firebase credentials
# Download from Firebase Console → Project Settings → Service Accounts
# Save as firebase-service-account.json

# 3. Configure
cp .env.example .env

# 4. Run
python main.py

# 5. Test
python test_endpoints.py
```

**API Docs**: http://localhost:8000/docs

## 📦 Architecture

```
├── main.py                     # FastAPI app entry point
├── config/
│   ├── settings.py             # Environment config
│   └── firebase_init.py        # Firebase Admin SDK
├── middleware/
│   └── auth.py                 # JWT token verification
├── routers/
│   ├── auth.py                 # POST /auth/login
│   ├── music.py                # 7 music endpoints
│   ├── recommend.py            # 9 recommendation endpoints
│   ├── smart_recommend.py      # 4 smart rec endpoints
│   ├── playlist.py             # 3 playlist endpoints
│   └── user.py                 # 4 user/library endpoints
├── services/
│   ├── youtube_service.py      # yt-dlp search + extraction + cache
│   ├── recommendation_service.py
│   ├── smart_recommendation.py
│   └── trusted_channels.py
└── models/
    └── schemas.py              # Pydantic models
```

## 🔑 Endpoints (27 total)

| Category | Count | Prefix |
|----------|-------|--------|
| Health | 2 | `/`, `/health` |
| Auth | 1 | `/auth` |
| Music | 7 | `/music` |
| Recommendations | 9 | `/recommend` |
| Smart Recs | 4 | `/recommend/smart` |
| Playlists | 3 | `/playlist` |
| User/Library | 4 | `/user`, `/library` |

See [API_REFERENCE.md](API_REFERENCE.md) for full details.

## 🐳 Docker

```bash
docker-compose up -d
```

## 🔧 Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | Server port |
| `HOST` | `0.0.0.0` | Server host |
| `FIREBASE_CREDENTIALS_PATH` | `firebase-service-account.json` | Firebase SA key |
| `FIREBASE_PROJECT_ID` | `sample-music-65323` | Firebase project |
| `CORS_ORIGINS` | `*` | Allowed origins |

## 📱 Flutter Integration

Set in your Flutter app's `.env`:
```
API_BASE_URL=http://<your-ip>:8000
```
