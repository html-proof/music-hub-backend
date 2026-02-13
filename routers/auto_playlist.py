"""
Auto-Playlist Router — AI-powered automatic playlist generation.
Algorithms: smart, most_played, liked_based, artist_based, mood_mix
Uses play history, likes, and keyword weights from Firebase RTDB.
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from datetime import datetime
from uuid import uuid4
import logging

from routers.auth import get_current_user
from services.firebase_db import music_db, _ref
from services.youtube_service import search_songs
from collections import Counter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auto-playlist", tags=["Auto-Playlists"])


# ==================== GENERATE ====================

@router.post("/generate")
async def generate_auto_playlist(
    algorithm: str = Query(
        "smart",
        enum=["smart", "most_played", "liked_based", "artist_based", "mood_mix"],
    ),
    current_user: dict = Depends(get_current_user),
):
    """
    Generate an automatic playlist based on user history.

    Algorithms:
    - **smart**: 40% liked + 30% most-played + 30% artist-based recommendations
    - **most_played**: Top songs by play count
    - **liked_based**: All liked songs as a playlist
    - **artist_based**: Discover more from top artists
    - **mood_mix**: Blend of user's top genre keywords
    """
    uid = current_user["uid"]

    try:
        if algorithm == "liked_based":
            songs, name, desc = await _liked_based(uid)
        elif algorithm == "most_played":
            songs, name, desc = await _most_played(uid)
        elif algorithm == "artist_based":
            songs, name, desc = await _artist_based(uid)
        elif algorithm == "mood_mix":
            songs, name, desc = await _mood_mix(uid)
        else:
            songs, name, desc = await _smart_mix(uid)

        if not songs:
            raise HTTPException(
                status_code=400,
                detail="Not enough listening history to generate a playlist. "
                       "Play and complete some songs first!",
            )

        # Store playlist in RTDB
        playlist_id = f"auto_{uid}_{algorithm}_{int(datetime.utcnow().timestamp())}"
        playlist_data = {
            "playlist_id": playlist_id,
            "name": name,
            "description": desc,
            "songs": songs,
            "song_count": len(songs),
            "created_at": datetime.utcnow().isoformat(),
            "algorithm": algorithm,
            "user_id": uid,
        }

        _ref(f"/auto_playlists/{playlist_id}").set(playlist_data)

        # Add to user's playlist index (keep last 20)
        _ref(f"/user_auto_playlists/{uid}/{playlist_id}").set({
            "playlist_id": playlist_id,
            "name": name,
            "song_count": len(songs),
            "algorithm": algorithm,
            "created_at": datetime.utcnow().isoformat(),
        })

        return playlist_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate playlist")


# ==================== RETRIEVE ====================

@router.get("/list")
async def get_user_auto_playlists(current_user: dict = Depends(get_current_user)):
    """Get all auto-generated playlists for the user (summaries only)."""
    uid = current_user["uid"]
    try:
        index = _ref(f"/user_auto_playlists/{uid}").get()
        if not index:
            return {"playlists": [], "total": 0}

        playlists = list(index.values())
        playlists.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return {"playlists": playlists[:20], "total": len(playlists)}
    except Exception as e:
        logger.error(f"Error getting playlists: {e}")
        return {"playlists": [], "total": 0}


@router.get("/{playlist_id}")
async def get_auto_playlist(playlist_id: str):
    """Get a specific auto-generated playlist with all songs."""
    try:
        data = _ref(f"/auto_playlists/{playlist_id}").get()
        if not data:
            raise HTTPException(status_code=404, detail="Playlist not found or expired")
        return data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting playlist: {e}")
        # Return detailed error for debugging
        raise HTTPException(status_code=500, detail=f"Failed to get playlist: {str(e)}")


@router.delete("/{playlist_id}")
async def delete_auto_playlist(
    playlist_id: str, current_user: dict = Depends(get_current_user),
):
    """Delete an auto-generated playlist."""
    uid = current_user["uid"]
    try:
        _ref(f"/auto_playlists/{playlist_id}").delete()
        _ref(f"/user_auto_playlists/{uid}/{playlist_id}").delete()
        return {"message": "Playlist deleted"}
    except Exception as e:
        logger.error(f"Error deleting playlist: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete playlist")


# ==================== CLEAR HISTORY ====================

@router.delete("/history/clear")
async def clear_user_history(current_user: dict = Depends(get_current_user)):
    """Clear ALL user history: plays, searches, keywords, activity log."""
    uid = current_user["uid"]
    try:
        _ref(f"/play_history/{uid}").delete()
        _ref(f"/search_history/{uid}").delete()
        _ref(f"/user_keywords/{uid}").delete()
        _ref(f"/activity_log/{uid}").delete()
        _ref(f"/recommendations_cache/{uid}").delete()

        # Reset stats but keep user profile
        _ref(f"/users/{uid}").update({
            "total_searches": 0,
            "total_plays": 0,
            "total_skips": 0,
            "total_completes": 0,
            "updated_at": datetime.utcnow().isoformat(),
        })

        return {"message": "All history cleared", "user_id": uid}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear history")


# ==================== ALGORITHM IMPLEMENTATIONS ====================

async def _liked_based(uid: str):
    """Playlist from user's liked songs in Firestore."""
    from config.firebase_init import get_firestore_client
    db = get_firestore_client()
    songs = []

    if db:
        try:
            docs = db.collection("users").document(uid).collection("favorites").stream()
            for doc in docs:
                data = doc.to_dict()
                songs.append({
                    "video_id": data.get("id", doc.id),
                    "title": data.get("title", ""),
                    "channel": data.get("artist", ""),
                    "thumbnail": data.get("thumbnailUrl", ""),
                })
        except Exception as e:
            logger.error(f"Liked-based error: {e}")

    return songs[:30], "💖 My Favorite Songs", f"Your {len(songs[:30])} most loved tracks"


async def _most_played(uid: str):
    """Top songs by play count from RTDB play history."""
    history = music_db.get_play_history(uid, limit=200)

    play_counts: Counter = Counter()
    video_data = {}

    for h in history:
        vid = h.get("video_id", "")
        if not vid:
            continue
        play_counts[vid] += 1
        if vid not in video_data:
            video_data[vid] = {
                "video_id": vid,
                "title": h.get("title", ""),
                "channel": h.get("artist", h.get("channel", "")),
                "thumbnail": f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg",
            }

    top = play_counts.most_common(30)
    songs = [video_data[vid] for vid, _ in top if vid in video_data]
    return songs, "🔥 Most Played", f"Your {len(songs)} most played songs"


async def _artist_based(uid: str):
    """Search for more songs from user's top artists."""
    history = music_db.get_play_history(uid, limit=200)

    artist_counts: Counter = Counter()
    for h in history:
        if h.get("status") == "completed":
            artist = h.get("artist", "")
            if artist and len(artist) > 1:
                artist_counts[artist] += 1

    top_artists = [a for a, _ in artist_counts.most_common(3)]

    if not top_artists:
        return [], "", ""

    songs = []
    for artist in top_artists:
        results = await search_songs(f"{artist} songs", limit=10)
        songs.extend(results)

    display = ", ".join(top_artists[:2])
    return (
        songs[:30],
        f"🎤 {display} Mix",
        f"More from your favorite artists",
    )


async def _mood_mix(uid: str):
    """Mix based on user's top keyword themes."""
    top_kw = music_db.get_user_top_keywords(uid, limit=10)

    if not top_kw:
        # Fallback to user moods if no keywords yet
        user = music_db.get_user(uid)
        moods = user.get("moods", ["chill"]) if user else ["chill"]
        search_terms = moods
    else:
        search_terms = [k["keyword"] for k in top_kw[:3]]

    songs = []
    for term in search_terms:
        results = await search_songs(f"{term} music", limit=10)
        songs.extend(results)

    display = ", ".join(search_terms[:2]).title()
    return (
        songs[:30],
        f"🌈 Mood Mix — {display}",
        "A blend of your favorite vibes",
    )


async def _smart_mix(uid: str):
    """Intelligent mix: 40% liked + 30% most-played + 30% artist recs."""
    liked, _, _ = await _liked_based(uid)
    most, _, _ = await _most_played(uid)

    # 40% liked (up to 12)
    smart_songs = liked[:12]

    # 30% most-played (up to 9, skip duplicates)
    seen_ids = {s.get("video_id") for s in smart_songs}
    for s in most:
        if s.get("video_id") not in seen_ids and len(smart_songs) < 21:
            smart_songs.append(s)
            seen_ids.add(s.get("video_id"))

    # 30% artist-based recs (up to 9)
    artist_songs, _, _ = await _artist_based(uid)
    for s in artist_songs:
        vid = s.get("id", s.get("video_id", ""))
        if vid not in seen_ids and len(smart_songs) < 30:
            smart_songs.append(s)
            seen_ids.add(vid)

    return smart_songs, "✨ Smart Mix", "Personalized mix based on your listening"
