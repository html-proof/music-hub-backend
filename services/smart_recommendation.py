"""
Smart Recommendation Service — time-aware, view-based quality filtering.
"""

import random
from datetime import datetime
from typing import List, Dict
from services.youtube_service import search_songs
from services.trusted_channels import get_trusted_channel_stats


# Quality tiers based on view count
QUALITY_LEVELS = {
    "high_quality": {
        "min_views": 1_000_000,
        "description": "Songs with 1M+ views — mainstream hits",
    },
    "medium_quality": {
        "min_views": 100_000,
        "description": "Songs with 100K+ views — popular tracks",
    },
    "emerging": {
        "min_views": 10_000,
        "description": "Songs with 10K+ views — rising artists",
    },
}

# Time-of-day mood mappings
TIME_MOOD_MAP = {
    "morning": {
        "mood": "calm",
        "queries": [
            "peaceful morning music",
            "morning chill playlist",
            "wake up gently songs",
            "calm morning vibes",
            "morning coffee music",
        ],
    },
    "afternoon": {
        "mood": "upbeat",
        "queries": [
            "afternoon vibes playlist",
            "feel good afternoon songs",
            "upbeat afternoon music",
            "midday energy playlist",
            "afternoon work music",
        ],
    },
    "evening": {
        "mood": "mellow",
        "queries": [
            "evening wind down music",
            "sunset vibes playlist",
            "evening relaxation songs",
            "chill evening playlist",
            "dinner music playlist",
        ],
    },
    "night": {
        "mood": "chill",
        "queries": [
            "late night chill music",
            "midnight vibes playlist",
            "night drive songs",
            "night study music",
            "after hours playlist",
        ],
    },
}


def get_time_context() -> dict:
    """Get the current time context."""
    now = datetime.now()

    hour = now.hour
    if 5 <= hour < 12:
        time_of_day = "morning"
    elif 12 <= hour < 17:
        time_of_day = "afternoon"
    elif 17 <= hour < 21:
        time_of_day = "evening"
    else:
        time_of_day = "night"

    month = now.month
    if month in (12, 1, 2):
        season = "winter"
    elif month in (3, 4, 5):
        season = "spring"
    elif month in (6, 7, 8):
        season = "summer"
    else:
        season = "fall"

    weekday_name = now.strftime("%A")
    month_name = now.strftime("%B")

    return {
        "year": now.year,
        "month": month_name,
        "month_num": month,
        "day": now.day,
        "weekday": weekday_name,
        "time_of_day": time_of_day,
        "is_weekend": now.weekday() >= 5,
        "season": season,
    }


async def get_smart_recommendations(
    limit: int = 30,
    quality: str = "medium_quality",
) -> dict:
    """Get smart, time-aware recommendations."""
    context = get_time_context()
    time_of_day = context["time_of_day"]

    # Get time-appropriate queries
    time_config = TIME_MOOD_MAP.get(time_of_day, TIME_MOOD_MAP["afternoon"])
    queries = time_config["queries"]

    # Add seasonal and weekend awareness
    if context["is_weekend"]:
        queries += ["weekend vibes playlist", "weekend chill music"]
    
    season = context["season"]
    queries.append(f"{season} vibes playlist")

    # Pick random queries and search
    selected_queries = random.sample(queries, min(3, len(queries)))

    all_results = []
    for query in selected_queries:
        results = await search_songs(query, limit=limit // len(selected_queries) + 5)
        all_results.extend(results)

    # Deduplicate by ID
    seen = set()
    unique_results = []
    for song in all_results:
        if song["id"] not in seen:
            seen.add(song["id"])
            unique_results.append(song)

    # Shuffle and limit
    random.shuffle(unique_results)
    final = unique_results[:limit]

    return {
        "success": True,
        "recommendations": final,
        "count": len(final),
        "quality_level": quality,
        "context": context,
    }


async def get_smart_feed(
    page: int = 1,
    page_size: int = 20,
) -> dict:
    """Get paginated smart feed for infinite scroll."""
    context = get_time_context()
    time_of_day = context["time_of_day"]
    time_config = TIME_MOOD_MAP.get(time_of_day, TIME_MOOD_MAP["afternoon"])

    # Different queries per page for variety
    all_queries = time_config["queries"] + [
        "trending songs this week",
        "top hits 2024",
        "new music today",
        "viral songs right now",
    ]

    # Rotate through queries based on page
    query_index = (page - 1) % len(all_queries)
    query = all_queries[query_index]

    results = await search_songs(query, limit=page_size + 5)
    results = results[:page_size]

    return {
        "success": True,
        "songs": results,
        "page": page,
        "page_size": page_size,
        "total": page_size * 10,  # Estimated total
        "has_more": page < 10,
        "context": context,
    }


def get_quality_stats() -> dict:
    """Get quality level stats and trusted channel info."""
    return {
        "quality_levels": QUALITY_LEVELS,
        "trusted_channels": get_trusted_channel_stats(),
    }
