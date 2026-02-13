"""
User Router — onboarding, preferences, profile, insights, and library endpoints.
Onboarding now creates user in Firebase RTDB for the recommendation engine.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional, List
from pydantic import BaseModel
from models.schemas import OnboardingRequest, LikeRequest
from middleware.auth import get_current_user, get_optional_user
from config.firebase_init import get_firestore_client
from services.firebase_db import music_db, Language, Mood
from services.smart_engine import smart_engine
from collections import Counter
import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(tags=["user"])


# ============================================================================
# /user/* endpoints
# ============================================================================

@router.get("/user/check-onboarding")
async def check_onboarding(user: dict = Depends(get_current_user)):
    """Check if user has completed onboarding."""
    uid = user["uid"]
    is_onboarded = music_db.is_user_onboarded(uid)

    if is_onboarded:
        rtdb_user = music_db.get_user(uid)
        return {"needs_onboarding": False, "user": rtdb_user}
    else:
        return {
            "needs_onboarding": True,
            "onboarding_steps": {
                "step_1": {
                    "title": "Choose Your Language",
                    "type": "single_select",
                    "options": [lang.value for lang in Language],
                },
                "step_2": {
                    "title": "Pick Your Moods (1-3)",
                    "type": "multi_select",
                    "min": 1,
                    "max": 3,
                    "options": [mood.value for mood in Mood],
                },
            },
        }


@router.post("/user/onboarding")
async def save_onboarding(request: OnboardingRequest, user: dict = Depends(get_current_user)):
    """Save onboarding preferences — creates user in RTDB + Firestore."""
    uid = user["uid"]

    # Validate moods
    if len(request.moods) < 1 or len(request.moods) > 3:
        raise HTTPException(status_code=400, detail="Select 1-3 moods")

    # Create user in RTDB (for recommendation engine)
    success = music_db.create_user(uid, request.language, request.moods)

    # Also save to Firestore (for profile)
    db = get_firestore_client()
    if db:
        try:
            db.collection("users").document(uid).collection("preferences").document("main").set({
                "selectedLanguage": request.language,
                "selectedMoods": request.moods,
                "favoriteGenres": request.genres,
                "updatedAt": datetime.datetime.now(),
            })
        except Exception as e:
            logger.error(f"Error saving to Firestore: {e}")

    if success:
        # Generate initial recommendations
        recs = smart_engine.generate_recommendations(uid, limit=20)
        return {"success": True, "message": "Welcome! Your music is ready.", "recommendations": recs}
    else:
        raise HTTPException(status_code=500, detail="Failed to save preferences")


@router.get("/user/preferences")
async def get_preferences(user: dict = Depends(get_current_user)):
    """Get user preferences from RTDB or Firestore."""
    uid = user["uid"]

    # Try RTDB first
    rtdb_user = music_db.get_user(uid)
    if rtdb_user:
        return {
            "selectedLanguage": rtdb_user.get("language", ""),
            "selectedMoods": rtdb_user.get("moods", []),
            "favoriteGenres": [],
        }

    # Fallback to Firestore
    db = get_firestore_client()
    if not db:
        return {"selectedLanguage": "", "selectedMoods": [], "favoriteGenres": []}

    try:
        doc = db.collection("users").document(uid).collection("preferences").document("main").get()
        if doc.exists:
            data = doc.to_dict()
            return {
                "selectedLanguage": data.get("selectedLanguage", ""),
                "selectedMoods": data.get("selectedMoods", []),
                "favoriteGenres": data.get("favoriteGenres", []),
            }
        return {"selectedLanguage": "", "selectedMoods": [], "favoriteGenres": []}
    except Exception as e:
        logger.error(f"Error getting preferences: {e}")
        return {"selectedLanguage": "", "selectedMoods": [], "favoriteGenres": []}


@router.post("/user/preferences")
async def save_preferences(request: OnboardingRequest, user: dict = Depends(get_current_user)):
    """Save/update user preferences."""
    uid = user["uid"]

    # Update RTDB
    try:
        from firebase_admin import db as rtdb
        rtdb.reference(f"/users/{uid}").update({
            "language": request.language,
            "moods": request.moods,
            "updated_at": datetime.datetime.utcnow().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error updating RTDB: {e}")

    # Also update Firestore
    db = get_firestore_client()
    if db:
        try:
            db.collection("users").document(uid).collection("preferences").document("main").set({
                "selectedLanguage": request.language,
                "selectedMoods": request.moods,
                "favoriteGenres": request.genres,
                "updatedAt": datetime.datetime.now(),
            }, merge=True)
        except Exception as e:
            logger.error(f"Error saving Firestore preferences: {e}")

    return {"success": True, "message": "Preferences updated"}


@router.get("/user/profile")
async def get_profile(user: dict = Depends(get_current_user)):
    """Get user profile with stats from RTDB."""
    uid = user["uid"]

    profile = {
        "uid": uid,
        "email": user.get("email", ""),
        "name": user.get("name", ""),
        "photoUrl": user.get("picture", ""),
    }

    # Enrich from RTDB
    rtdb_user = music_db.get_user(uid)
    if rtdb_user:
        profile.update({
            "language": rtdb_user.get("language"),
            "moods": rtdb_user.get("moods", []),
            "stats": {
                "total_searches": rtdb_user.get("total_searches", 0),
                "total_plays": rtdb_user.get("total_plays", 0),
                "total_skips": rtdb_user.get("total_skips", 0),
                "total_completes": rtdb_user.get("total_completes", 0),
            },
            "is_onboarded": rtdb_user.get("is_onboarded", False),
        })

    # Also enrich from Firestore
    db = get_firestore_client()
    if db:
        try:
            doc = db.collection("users").document(uid).get()
            if doc.exists:
                data = doc.to_dict()
                profile["email"] = data.get("email", profile["email"])
                profile["name"] = data.get("displayName", profile["name"])
                profile["photoUrl"] = data.get("photoUrl", profile["photoUrl"])
        except Exception as e:
            logger.error(f"Error fetching Firestore profile: {e}")

    return profile


@router.get("/user/insights")
async def get_user_insights(user: dict = Depends(get_current_user)):
    """Get user insights — top keywords, top artists, recent plays."""
    uid = user["uid"]

    top_keywords = music_db.get_user_top_keywords(uid, limit=10)
    play_history = music_db.get_play_history(uid, limit=50)

    artists: Counter = Counter()
    for play in play_history:
        if play.get("status") == "completed":
            artist = play.get("artist", "")
            if artist:
                artists[artist] += 1

    return {
        "top_keywords": top_keywords,
        "top_artists": [{"artist": a, "count": c} for a, c in artists.most_common(5)],
        "recent_plays": play_history[:10],
    }


@router.get("/user/home-feed")
async def get_home_feed(user: dict = Depends(get_current_user)):
    """Get personalized home feed based on all stored data."""
    uid = user["uid"]

    # Try cached first
    cached = smart_engine.get_cached_recommendations(uid)
    if cached:
        recs = cached
    else:
        recs = smart_engine.generate_recommendations(uid, limit=30)
        smart_engine.cache_recommendations(uid)

    rtdb_user = music_db.get_user(uid)

    return {
        "user_id": uid,
        "language": rtdb_user.get("language") if rtdb_user else None,
        "moods": rtdb_user.get("moods", []) if rtdb_user else [],
        "stats": {
            "total_searches": rtdb_user.get("total_searches", 0),
            "total_plays": rtdb_user.get("total_plays", 0),
            "total_skips": rtdb_user.get("total_skips", 0),
            "total_completes": rtdb_user.get("total_completes", 0),
        } if rtdb_user else {},
        "recommendations": recs,
    }


# ============================================================================
# /library/* endpoints
# ============================================================================

@router.post("/library/like")
async def like_song(request: LikeRequest, user: dict = Depends(get_current_user)):
    """Like or unlike a song (toggle). Also logs activity in RTDB."""
    uid = user["uid"]
    db = get_firestore_client()

    if not db:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        fav_ref = db.collection("users").document(uid).collection("favorites").document(request.song_id)
        doc = fav_ref.get()

        if doc.exists:
            fav_ref.delete()
            return {"success": True, "liked": False, "message": "Song unliked"}
        else:
            fav_ref.set({
                "id": request.song_id,
                "title": request.title,
                "artist": request.artist,
                "thumbnailUrl": request.thumbnailUrl,
                "audioUrl": request.audioUrl,
                "durationSeconds": request.durationSeconds,
                "timestamp": datetime.datetime.now(),
            })

            # Also boost keywords in RTDB when user likes a song
            from services.keyword_extractor import KeywordExtractor
            kw = KeywordExtractor()
            keywords = kw.extract_from_song_data(request.title, request.artist, "english")
            music_db._update_user_keywords(uid, keywords["all_keywords"], weight=3.0, context="like")

            return {"success": True, "liked": True, "message": "Song liked"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error toggling like: {str(e)}")
