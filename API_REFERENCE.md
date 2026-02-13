# 📖 API Reference — Music Hub Backend

Base URL: `http://localhost:8000`

---

## Health

### `GET /`
Health check.
```json
{ "status": "ok", "service": "Music Hub Backend", "version": "2.0.0" }
```

### `GET /health`
Detailed health with endpoint listing.

---

## 🔐 Auth

### `POST /auth/login`
Verify Firebase ID token and sync user.

**Request:**
```json
{ "id_token": "eyJhbGciOi..." }
```

**Response:**
```json
{
  "user": { "uid": "abc123", "email": "user@example.com", "name": "John", "photoUrl": "..." },
  "onboarding_required": true,
  "has_preferences": false
}
```

---

## 🎵 Music

### `GET /music/search?q={query}`
Search YouTube for songs.

**Response:**
```json
{
  "results": [
    { "id": "dQw4w9WgXcQ", "title": "Never Gonna Give You Up", "artist": "Rick Astley", "thumbnailUrl": "...", "audioUrl": "", "durationSeconds": 213 }
  ]
}
```

### `GET /music/play?id={videoId}&quality={high|medium|low}`
### `POST /music/play` — Body: `{ "id": "...", "quality": "high" }`
Resolve audio stream URL.

**Response:**
```json
{
  "success": true,
  "data": { "stream_url": "https://...", "url": "https://...", "title": "...", "artist": "...", "duration": 213 }
}
```

### `GET /music/play-48k?id={videoId}`
Low quality (48kbps) stream.

### `GET /music/play-64k?id={videoId}`
Medium quality (64kbps) stream.

### `GET /music/preview?id={videoId}`
### `POST /music/preview` — Body: `{ "id": "..." }`
Preview stream URL (capped at 30s).

### `GET /music/resolve?id={videoId}&quality={quality}`
Resolve direct URL without proxying.

### `POST /music/prefetch`
Warm cache for upcoming songs.

**Request:**
```json
{ "ids": ["id1", "id2", "id3"], "quality": "high" }
```

---

## 🎯 Recommendations

All return: `{ "success": true, "data": [SongResponse, ...] }`

| Endpoint | Params | Description |
|----------|--------|-------------|
| `GET /recommend/personalized` | — | Home screen recs |
| `GET /recommend/for-you` | `uid` | For You section |
| `GET /recommend/daily-mix` | `uid` | Daily Mix |
| `GET /recommend/because-liked` | `uid` | Based on likes |
| `GET /recommend/discover-weekly` | `uid` | Weekly discovery |
| `GET /recommend/mood` | `uid`, `mood` | Mood-based |
| `GET /recommend/type` | `type`, `language` | Genre/type |
| `GET /recommend/artist` | `name`, `language` | Artist-based |
| `GET /recommend/similar` | `id` | Similar to song |

---

## 🧠 Smart Recommendations

### `GET /recommend/smart/recommendations?limit=30&quality=medium_quality`
Time-aware, quality-filtered recommendations.

**Response:**
```json
{
  "success": true,
  "recommendations": [SongResponse, ...],
  "count": 30,
  "quality_level": "medium_quality",
  "context": { "time_of_day": "evening", "weekday": "Thursday", "season": "winter", ... }
}
```

### `GET /recommend/smart/feed?page=1&page_size=20`
Paginated feed for infinite scroll.

### `GET /recommend/smart/time-context`
Current time context (debug).

### `GET /recommend/smart/quality-stats`
Quality tiers and trusted channel counts.

---

## 📋 Playlists *(auth required)*

### `GET /playlist/my`
Get user's playlists.

### `POST /playlist/create`
```json
{ "name": "My Playlist" }
```

### `POST /playlist/{playlistId}/add`
```json
{ "song_id": "dQw4w9WgXcQ" }
```

---

## 👤 User *(auth required)*

### `POST /user/onboarding`
```json
{ "language": "English", "moods": ["happy", "chill"], "genres": ["pop", "rock"] }
```

### `GET /user/preferences`
Returns saved preferences.

### `POST /user/preferences`
Update preferences (same body as onboarding).

### `GET /user/profile`
Returns user profile from Firestore.

### `POST /library/like`
Toggle like on a song.
```json
{ "song_id": "dQw4w9WgXcQ", "title": "...", "artist": "...", "thumbnailUrl": "...", "durationSeconds": 213 }
```

---

## 📝 Song Response Schema

```json
{
  "id": "string",
  "title": "string",
  "artist": "string",
  "thumbnailUrl": "string",
  "audioUrl": "string",
  "durationSeconds": 0
}
```
