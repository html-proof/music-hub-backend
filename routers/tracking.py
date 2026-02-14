"""
Tracking router — Track all user actions in Firebase Realtime Database.
Search, play, skip, complete, search suggestions, and activity logs.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List
from routers.auth import get_current_user
from middleware.auth import get_optional_user
from services.firebase_db import music_db
from services.smart_engine import smart_engine
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/track", tags=["Tracking"])


# ==================== REQUEST MODELS ====================

class TrackSearchRequest(BaseModel):
    search_query: str
    results_count: int = 0
    clicked_result: Optional[str] = None


class TrackPlayRequest(BaseModel):
    video_id: str
    title: str
    artist: str = ""
    channel: str = ""
    duration: int = 0


class TrackSkipRequest(BaseModel):
    play_id: str
    play_duration: int = 0


class TrackCompleteRequest(BaseModel):
    play_id: str
    play_duration: int = 0


class ClickResultRequest(BaseModel):
    search_id: str
    video_id: str


# ==================== TRACKING ENDPOINTS ====================

@router.post("/search")
async def track_search(req: TrackSearchRequest,
                       current_user: Optional[dict] = Depends(get_optional_user)):
    """Track a search query — extracts keywords and updates user weights."""
    if not current_user:
        return {"status": "anonymous_ignored"}

    uid = current_user["uid"]
    search_id = music_db.track_search(uid, req.search_query, req.results_count, req.clicked_result)
    if not search_id:
        # Don't fail the request if tracking fails, just log it
        logger.warning(f"Failed to track search for {uid}")
        return {"status": "error", "message": "Failed to track"}
        
    return {"search_id": search_id, "status": "tracked"}


@router.post("/play")
async def track_play(req: TrackPlayRequest,
                     current_user: Optional[dict] = Depends(get_optional_user)):
    """Track when user starts playing a song."""
    if not current_user:
        return {"status": "anonymous_playing"}

    uid = current_user["uid"]
    play_id = music_db.track_play(
        uid, req.video_id, req.title, req.artist, req.channel, req.duration,
    )
    if not play_id:
        logger.warning(f"Failed to track play for {uid}")
        return {"status": "error"}
        
    return {"play_id": play_id, "status": "playing"}


@router.post("/skip")
async def track_skip(req: TrackSkipRequest,
                     current_user: Optional[dict] = Depends(get_optional_user)):
    """Track skip — penalizes keywords if skipped early (<20%)."""
    if not current_user:
        return {"status": "anonymous_skipped"}

    uid = current_user["uid"]
    music_db.track_skip(uid, req.play_id, req.play_duration)
    # Refresh recommendation cache in background
    smart_engine.cache_recommendations(uid)
    return {"status": "skip_tracked"}


@router.post("/complete")
async def track_complete(req: TrackCompleteRequest,
                         current_user: Optional[dict] = Depends(get_optional_user)):
    """Track completion — heavily boosts keyword weights."""
    if not current_user:
        return {"status": "anonymous_completed"}

    uid = current_user["uid"]
    music_db.track_complete(uid, req.play_id, req.play_duration)
    # Refresh recommendation cache in background
    smart_engine.cache_recommendations(uid)
    return {"status": "complete_tracked"}


@router.post("/click")
async def track_click(req: ClickResultRequest,
                      current_user: Optional[dict] = Depends(get_optional_user)):
    """Track which search result was clicked."""
    if not current_user:
        return {"status": "anonymous_click"}

    uid = current_user["uid"]
    try:
        from firebase_admin import db as rtdb
        rtdb.reference(f"/search_history/{uid}/{req.search_id}").update({
            "clicked_result": req.video_id,
        })
        return {"status": "click_tracked"}
    except Exception as e:
        logger.error(f"Error tracking click: {e}")
        # Don't crash for analytics errors
        return {"status": "error", "message": str(e)}


# ==================== HISTORY ENDPOINTS ====================

@router.get("/search-history")
async def get_search_history(limit: int = 50,
                             current_user: dict = Depends(get_current_user)):
    """Get user's recent search history."""
    uid = current_user["uid"]
    searches = music_db.get_user_searches(uid, limit)
    return {"searches": searches, "count": len(searches)}


@router.get("/play-history")
async def get_play_history(limit: int = 100,
                           current_user: dict = Depends(get_current_user)):
    """Get user's play history with status (playing/skipped/completed)."""
    uid = current_user["uid"]
    plays = music_db.get_play_history(uid, limit)
    return {"plays": plays, "count": len(plays)}


@router.get("/activity-log")
async def get_activity_log(limit: int = 100,
                           current_user: dict = Depends(get_current_user)):
    """Get full activity log."""
    uid = current_user["uid"]
    activities = music_db.get_user_activity_log(uid, limit)
    return {"activities": activities, "count": len(activities)}


@router.get("/keywords")
async def get_user_keywords(limit: int = 30,
                            current_user: dict = Depends(get_current_user)):
    """Get user's top keywords with weights — the DNA of their taste."""
    uid = current_user["uid"]
    keywords = music_db.get_user_top_keywords(uid, limit)
    return {"keywords": keywords, "count": len(keywords)}


@router.get("/suggestions")
async def get_search_suggestions(q: str = "",
                                 current_user: dict = Depends(get_current_user)):
    """Autocomplete suggestions from user's keywords and history."""
    if not q or len(q) < 2:
        return {"suggestions": []}
    uid = current_user["uid"]
    suggestions = smart_engine.get_search_suggestions(uid, q, limit=10)
    return {"suggestions": suggestions}
