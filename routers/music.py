"""
Music Router — search, playback, preview, resolve, prefetch endpoints.
"""

import asyncio
from fastapi import APIRouter, Query, BackgroundTasks
from fastapi.responses import RedirectResponse
from typing import Optional
from models.schemas import PlayRequest, PrefetchRequest
from services.youtube_service import search_songs, get_stream_url, prefetch_songs

router = APIRouter(prefix="/music", tags=["music"])


@router.get("/search")
async def search(q: str = Query(..., description="Search query")):
    """Search YouTube for songs."""
    results = await search_songs(q, limit=15)
    return {"results": results}


@router.post("/search")
async def search_post(q: str = Query(..., description="Search query")):
    """Search YouTube for songs (POST variant)."""
    results = await search_songs(q, limit=15)
    return {"results": results}


@router.get("/play")
async def play_get(
    id: str = Query(..., description="YouTube video ID"),
    quality: str = Query("high", description="Audio quality"),
    force_refresh: bool = Query(False, description="Bypass cache and fetch fresh URL"),
):
    """Get audio stream URL for a video."""
    result = await get_stream_url(id, quality=quality, force_refresh=force_refresh)

    if not result or not result.get("stream_url"):
        return {"success": False, "message": "Could not resolve stream URL"}

    return {
        "success": True,
        "data": {
            "stream_url": result["stream_url"],
            "url": result["stream_url"],
            "title": result.get("title", ""),
            "artist": result.get("artist", ""),
            "duration": result.get("duration", 0),
            "thumbnail": result.get("thumbnail", ""),
        }
    }


@router.post("/play")
async def play_post(request: PlayRequest):
    """Get audio stream URL for a video (POST variant)."""
    video_id = request.id or request.videoId
    if not video_id:
        return {"success": False, "message": "Missing video ID"}

    result = await get_stream_url(video_id, quality=request.quality)

    if not result or not result.get("stream_url"):
        return {"success": False, "message": "Could not resolve stream URL"}

    return {
        "success": True,
        "data": {
            "stream_url": result["stream_url"],
            "url": result["stream_url"],
            "title": result.get("title", ""),
            "artist": result.get("artist", ""),
            "duration": result.get("duration", 0),
            "thumbnail": result.get("thumbnail", ""),
        }
    }


@router.get("/play-48k")
async def play_48k(id: str = Query(..., description="YouTube video ID")):
    """Get low quality (48kbps) audio stream URL."""
    result = await get_stream_url(id, quality="48k")

    if not result or not result.get("stream_url"):
        return {"success": False, "message": "Could not resolve stream URL"}

    return {
        "success": True,
        "data": {
            "stream_url": result["stream_url"],
            "url": result["stream_url"],
        }
    }


@router.get("/play-64k")
async def play_64k(id: str = Query(..., description="YouTube video ID")):
    """Get medium quality (64kbps) audio stream URL."""
    result = await get_stream_url(id, quality="64k")

    if not result or not result.get("stream_url"):
        return {"success": False, "message": "Could not resolve stream URL"}

    return {
        "success": True,
        "data": {
            "stream_url": result["stream_url"],
            "url": result["stream_url"],
        }
    }


@router.get("/preview")
async def preview_get(id: str = Query(..., description="YouTube video ID")):
    """Get preview stream URL for a video."""
    result = await get_stream_url(id, quality="low")

    if not result or not result.get("stream_url"):
        return {"success": False, "message": "Could not resolve preview URL"}

    return {
        "success": True,
        "data": {
            "stream_url": result["stream_url"],
            "url": result["stream_url"],
            "title": result.get("title", ""),
            "artist": result.get("artist", ""),
            "duration": min(result.get("duration", 30), 30),  # Cap at 30s
        }
    }


@router.post("/preview")
async def preview_post(request: PlayRequest):
    """Get preview stream URL (POST variant)."""
    video_id = request.id or request.videoId
    if not video_id:
        return {"success": False, "message": "Missing video ID"}

    result = await get_stream_url(video_id, quality="low")

    if not result or not result.get("stream_url"):
        return {"success": False, "message": "Could not resolve preview URL"}

    return {
        "success": True,
        "data": {
            "stream_url": result["stream_url"],
            "url": result["stream_url"],
            "title": result.get("title", ""),
            "artist": result.get("artist", ""),
            "duration": min(result.get("duration", 30), 30),
        }
    }


@router.get("/resolve")
async def resolve(
    id: str = Query(..., description="YouTube video ID"),
    quality: str = Query("high", description="Audio quality"),
):
    """Resolve direct stream URL without proxying."""
    result = await get_stream_url(id, quality=quality)

    if not result or not result.get("stream_url"):
        return {"success": False, "message": "Could not resolve URL"}

    return {
        "success": True,
        "data": {
            "stream_url": result["stream_url"],
            "url": result["stream_url"],
            "title": result.get("title", ""),
            "artist": result.get("artist", ""),
            "duration": result.get("duration", 0),
        }
    }


@router.post("/prefetch")
async def prefetch(request: PrefetchRequest, background_tasks: BackgroundTasks):
    """Warm cache for a list of video IDs."""
    if not request.ids:
        return {"success": True, "message": "No IDs to prefetch"}

    # Run prefetch in background
    background_tasks.add_task(prefetch_songs, request.ids, request.quality)

    return {
        "success": True,
        "message": f"Prefetching {len(request.ids)} songs",
        "ids": request.ids,
    }
