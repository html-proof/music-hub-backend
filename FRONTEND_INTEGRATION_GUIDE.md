# 📱 Frontend Integration Guide — Music Hub

This guide bridges the gap between the Music Hub Backend and your Frontend application. It outlines the core features, key endpoints, and the "logic flows" required for a premium Spotify-like experience.

---

## 🏗️ Architecture Overview

The backend uses a hybrid architecture to maximize performance and personalization:
1.  **Firebase Auth**: The ONLY source of truth for user identity.
2.  **Firebase Firestore**: Stores static user data like Profiles, User Playlists, and Favorites.
3.  **Firebase RTDB**: Stores high-frequency data like Listening History, Taste DNA (Keywords), and Auto-Playlists.
4.  **In-Memory Cache**: Backend caches YouTube results and stream URLs for sub-50ms repeat access.

---

## 🔑 Key Integration Flows

### 1. Authentication & Onboarding
The system is designed for "Social Login First".
- **Step 1**: Frontend performs Google Sign-In and gets a **Firebase ID Token**.
- **Step 2**: Send token to `POST /auth/login`.
    - Returns `onboarding_required: true` if it's a new user.
- **Step 3**: If required, send user to Onboarding Screen.
    - Submit choices to `POST /user/onboarding`.
    - This triggers initial recommendation generation.

### 2. The Home Screen (Personalization)
The "Home Feed" is the heart of the app.
- **Main Feed**: `GET /user/home-feed`.
    - Returns a blend of languages, moods, and specific recommendations.
- **Infinite Scroll**: Use `GET /recommend/smart/feed?page=X`.
    - Provides a continuous stream of time-aware recommendations.

### 3. Search & The "Taste DNA"
- **Autocomplete**: As the user types, call `GET /track/suggestions?q=...`.
    - These suggestions are weighted by the user's past searches and "DNA" (top keywords).
- **Search Results**: `GET /music/search?q=...`.
- **Tracking**: IMPORTANT! When a user clicks a result, call `POST /track/click` with the `search_id` and `video_id`. This helps the AI learn what they actually like.

### 4. Player & Analytics (The Feedback Loop)
To make recommendations smart, the backend needs to know what happens in the player:
- **Start Play**: `POST /track/play`.
- **Skip**: `POST /track/skip`. If skipped <20%, the backend penalizes the channel/song.
- **Completion**: `POST /track/complete`. This heavily boosts the song's genre/keywords in the user's taste profile.

### 5. AI-Powered "Auto-Playlists"
Don't just show static lists. Offer dynamic AI mixes:
- **Algorithms**: `smart`, `most_played`, `liked_based`, `artist_based`, `mood_mix`.
- **Usage**: Call `POST /auto-playlist/generate?algorithm=smart`.
- **Management**: User can see all their generated mixes at `GET /auto-playlist/list`.

---

## 📊 Essential Data Models

### Song Object
Standardized across all endpoints:
```json
{
  "id": "videoId",
  "title": "Song Title",
  "artist": "Artist/Channel",
  "thumbnailUrl": "https://...",
  "audioUrl": "...", // May be empty, use /music/play to resolve
  "durationSeconds": 240
}
```

### User Insights ("Taste DNA")
Show users why they get certain recommendations:
- `GET /user/insights` returns:
    - **Top Keywords**: (e.g., "Lofi", "Chill", "Binaural")
    - **Top Artists**: Most completed tracks.
    - **Recent History**: The 50 most recent actions.

---

## 🛠️ Tips for High-Performance UI
1.  **Prefetching**: When the user is on the last 30s of a song, call `POST /music/prefetch` with the next 3 IDs in the queue.
2.  **Debounce Suggestions**: Don't hit `/track/suggestions` on every keystroke. 300ms debounce is ideal.
3.  **Optimistic UI**: When "Liking" a song, update the heart icon immediately and call `POST /library/like` in the background.

---

## 📡 API Reference Links
For the full list of 27+ endpoints and exact JSON schemas, see:
- [API_REFERENCE.md](file:///e:/Backend/API_REFERENCE.md)
- `/docs` (Swagger UI when running locally)
