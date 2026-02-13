"""
Recommendation Router — personalized, for-you, daily-mix, mood, artist, similar endpoints.
"""

from fastapi import APIRouter, Query, Depends
from typing import Optional
from services import recommendation_service as rec
from services.firebase_db import music_db
from middleware.auth import get_current_user, get_optional_user

router = APIRouter(prefix="/recommend", tags=["recommendations"])


@router.get("/personalized")
async def personalized():
    """Get personalized home screen recommendations."""
    results = await rec.get_personalized_recommendations(limit=20)
    return {"success": True, "data": results}


@router.get("/for-you")
async def for_you(uid: str = Query("", description="User ID")):
    """Get 'For You' recommendations."""
    results = await rec.get_for_you(uid, limit=20)
    return {"success": True, "data": results}


@router.get("/daily-mix")
async def daily_mix(uid: str = Query("", description="User ID")):
    """Get daily mix recommendations."""
    results = await rec.get_daily_mix(uid, limit=20)
    return {"success": True, "data": results}


@router.get("/because-liked")
async def because_liked(uid: str = Query("", description="User ID")):
    """Get recommendations based on liked songs."""
    results = await rec.get_because_liked(uid, limit=20)
    return {"success": True, "data": results}


@router.get("/discover-weekly")
async def discover_weekly(uid: str = Query("", description="User ID")):
    """Get discover weekly recommendations."""
    results = await rec.get_discover_weekly(uid, limit=20)
    return {"success": True, "data": results}


@router.get("/mood")
async def mood_recommendations(
    uid: str = Query("", description="User ID"),
    mood: str = Query("chill", description="Mood name"),
):
    """Get mood-based recommendations."""
    results = await rec.get_mood_recommendations(uid, mood, limit=20)
    return {"success": True, "data": results}


@router.get("/type")
async def by_type(
    type: str = Query(..., description="Genre/type"),
    language: str = Query("", description="Language filter"),
):
    """Get recommendations by genre/type."""
    results = await rec.get_by_type(type, language, limit=20)
    return {"success": True, "data": results}


@router.get("/artist")
async def by_artist(
    name: str = Query(..., description="Artist name"),
    language: str = Query("", description="Language filter"),
):
    """Get recommendations by artist."""
    results = await rec.get_by_artist(name, language, limit=20)
    return {"success": True, "data": results}


@router.get("/similar")
async def similar_songs(id: str = Query(..., description="Video ID")):
    """Get songs similar to a given video."""
    results = await rec.get_similar(id, limit=20)
    return {"success": True, "data": results}


@router.get("/home-feed")
async def home_feed(user: dict = Depends(get_current_user)):
    """
    Get personalized home feed based on user's language and moods from RTDB.
    Requires authentication — reads user's preferences from Firebase RTDB.
    """
    import logging
    logger = logging.getLogger(__name__)

    uid = user.get("uid", "")
    language = "english"
    moods = ["chill"]

    if uid:
        rtdb_user = music_db.get_user(uid)
        logger.info(f"[home-feed] uid={uid}, rtdb_user={rtdb_user}")

        if rtdb_user:
            language = rtdb_user.get("language", "english")
            moods = rtdb_user.get("moods", ["chill"])
        else:
            logger.warning(f"[home-feed] No RTDB user found for uid={uid}, using defaults")
    else:
        logger.warning("[home-feed] No uid in auth token")

    logger.info(f"[home-feed] Using language={language}, moods={moods}")

    sections = await rec.get_language_mood_feed(language, moods, limit=15)

    return {
        "success": True,
        "language": language,
        "moods": moods,
        "sections": sections,
    }

@router.get("/by-language")
async def by_language(
    language: str = Query("english", description="Language"),
    mood: str = Query("", description="Optional mood filter"),
):
    """Get recommendations filtered by language and optional mood."""
    if mood:
        query = f"{mood} {language} songs"
    else:
        from datetime import datetime
        y = datetime.now().year
        lang_queries = rec._language_queries().get(
            language.lower(),
            [f"top {language} songs {y}"]
        )
        import random
        query = random.choice(lang_queries)

    from services.youtube_service import search_songs
    results = await search_songs(query, limit=20)
    return {"success": True, "data": results}
