"""
Recommendation Service — YouTube-based recommendations with genre, mood, artist logic.
"""

import random
from typing import List, Optional
from services.youtube_service import search_songs


# Genre-specific search queries for diverse recommendations
GENRE_QUERIES = {
    "pop": ["top pop hits 2024", "best pop songs", "trending pop music", "pop hits playlist"],
    "rock": ["best rock songs", "classic rock hits", "modern rock playlist", "rock anthems"],
    "hiphop": ["top hip hop 2024", "best rap songs", "trending hip hop", "rap hits playlist"],
    "rnb": ["best r&b songs 2024", "rnb hits playlist", "smooth rnb", "r&b love songs"],
    "electronic": ["best electronic music", "edm hits 2024", "trending electronic", "chill electronic"],
    "classical": ["beautiful classical music", "classical piano", "classical orchestra", "relaxing classical"],
    "jazz": ["smooth jazz", "best jazz songs", "jazz piano", "jazz classics"],
    "country": ["top country songs 2024", "best country hits", "country music playlist"],
    "latin": ["top latin hits 2024", "reggaeton hits", "latin pop 2024", "bachata hits"],
    "indie": ["best indie songs 2024", "indie rock playlist", "indie pop hits", "indie folk"],
    "bollywood": ["latest bollywood songs 2024", "best hindi songs", "bollywood hits playlist"],
    "kpop": ["top kpop songs 2024", "best kpop hits", "trending kpop", "kpop playlist"],
}

MOOD_QUERIES = {
    "happy": ["happy songs playlist", "feel good music", "upbeat songs 2024", "cheerful music"],
    "sad": ["sad songs playlist", "emotional songs", "heartbreak songs", "melancholy music"],
    "energetic": ["workout music", "high energy songs", "pump up playlist", "gym music"],
    "chill": ["chill music playlist", "relaxing songs", "chill vibes", "lofi chill"],
    "romantic": ["romantic songs", "love songs playlist", "romance music", "couples playlist"],
    "focus": ["focus music", "study music", "concentration playlist", "deep focus"],
    "party": ["party music 2024", "dance hits", "party playlist", "club music"],
    "sleep": ["sleep music", "calming music", "bedtime songs", "peaceful music"],
}

TIME_OF_DAY_QUERIES = {
    "morning": ["morning vibes playlist", "wake up songs", "good morning music", "morning motivation"],
    "afternoon": ["afternoon chill", "midday music", "afternoon vibes", "feel good afternoon"],
    "evening": ["evening chill music", "sunset vibes", "evening relaxation", "dinner music"],
    "night": ["late night vibes", "night drive music", "midnight playlist", "night chill"],
}


async def get_personalized_recommendations(limit: int = 20) -> List[dict]:
    """Get personalized recommendations (general trending + diverse genres)."""
    queries = [
        "trending songs 2024",
        "top hits this week",
        "new music releases 2024",
        "popular songs right now",
    ]
    query = random.choice(queries)
    results = await search_songs(query, limit=limit)
    return results


async def get_for_you(uid: str, limit: int = 20) -> List[dict]:
    """Get 'For You' recommendations."""
    queries = [
        "recommended songs 2024",
        "songs you might like",
        "discover new music 2024",
        "best songs this month",
    ]
    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_daily_mix(uid: str, limit: int = 20) -> List[dict]:
    """Get daily mix recommendations."""
    queries = [
        "daily mix playlist",
        "mix of the day",
        "top 50 global",
        "hit songs today",
    ]
    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_because_liked(uid: str, limit: int = 20) -> List[dict]:
    """Get recommendations based on liked songs."""
    queries = [
        "songs similar to popular hits",
        "if you like pop try these",
        "discover similar music",
        "trending similar songs",
    ]
    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_discover_weekly(uid: str, limit: int = 20) -> List[dict]:
    """Get discover weekly recommendations."""
    queries = [
        "discover new artists 2024",
        "hidden gems music",
        "underrated songs 2024",
        "new music friday",
    ]
    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_mood_recommendations(uid: str, mood: str, limit: int = 20) -> List[dict]:
    """Get mood-based recommendations."""
    mood_lower = mood.lower()
    queries = MOOD_QUERIES.get(mood_lower, [f"{mood} music playlist", f"{mood} songs"])
    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_by_type(category_type: str, language: str = "", limit: int = 20) -> List[dict]:
    """Get recommendations by genre/type."""
    type_lower = category_type.lower()
    queries = GENRE_QUERIES.get(type_lower, [f"{category_type} music playlist", f"best {category_type} songs"])

    if language:
        queries = [f"{q} {language}" for q in queries]

    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_by_artist(artist: str, language: str = "", limit: int = 20) -> List[dict]:
    """Get recommendations by artist."""
    query = f"{artist} songs"
    if language:
        query += f" {language}"
    return await search_songs(query, limit=limit)


async def get_similar(video_id: str, limit: int = 20) -> List[dict]:
    """Get similar songs to a given video."""
    import yt_dlp
    import asyncio

    # First get the title of the original song
    def _get_title():
        opts = {"quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=False)
                return info.get("title", "") if info else ""
        except:
            return ""

    loop = asyncio.get_event_loop()
    title = await loop.run_in_executor(None, _get_title)

    if title:
        query = f"songs like {title}"
        return await search_songs(query, limit=limit)

    return await search_songs("popular songs 2024", limit=limit)
