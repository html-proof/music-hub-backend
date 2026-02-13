"""
Recommendation Router — personalized, for-you, daily-mix, mood, artist, similar endpoints.
"""

from fastapi import APIRouter, Query
from typing import Optional
from services import recommendation_service as rec

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
