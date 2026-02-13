"""
Smart Recommendation Router — time-aware, quality-filtered recommendations.
"""

from fastapi import APIRouter, Query
from services.smart_recommendation import (
    get_smart_recommendations,
    get_smart_feed,
    get_time_context,
    get_quality_stats,
)

router = APIRouter(prefix="/recommend/smart", tags=["smart-recommendations"])


@router.get("/recommendations")
async def smart_recommendations(
    limit: int = Query(30, description="Number of recommendations"),
    quality: str = Query("medium_quality", description="Quality level"),
):
    """Get smart, time-aware recommendations."""
    result = await get_smart_recommendations(limit=limit, quality=quality)
    return result


@router.get("/feed")
async def smart_feed(
    page: int = Query(1, description="Page number"),
    page_size: int = Query(20, description="Items per page"),
):
    """Get paginated smart feed for infinite scroll."""
    result = await get_smart_feed(page=page, page_size=page_size)
    return result


@router.get("/time-context")
async def time_context():
    """Get current time context."""
    ctx = get_time_context()
    return {"success": True, "context": ctx}


@router.get("/quality-stats")
async def quality_stats():
    """Get quality level stats and trusted channel info."""
    stats = get_quality_stats()
    return stats
