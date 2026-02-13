"""
Recommendation Service — YouTube-based recommendations with genre, mood, artist logic.
Uses dynamic current year for all search queries.
"""

import random
from datetime import datetime
from typing import List, Optional
from services.youtube_service import search_songs


def _year():
    """Get current year for dynamic search queries."""
    return datetime.now().year


# Genre-specific search queries for diverse recommendations
def _genre_queries():
    y = _year()
    return {
        "pop": [f"top pop hits {y}", "best pop songs", "trending pop music", "pop hits playlist"],
        "rock": ["best rock songs", "classic rock hits", "modern rock playlist", "rock anthems"],
        "hiphop": [f"top hip hop {y}", "best rap songs", "trending hip hop", "rap hits playlist"],
        "rnb": [f"best r&b songs {y}", "rnb hits playlist", "smooth rnb", "r&b love songs"],
        "electronic": ["best electronic music", f"edm hits {y}", "trending electronic", "chill electronic"],
        "classical": ["beautiful classical music", "classical piano", "classical orchestra", "relaxing classical"],
        "jazz": ["smooth jazz", "best jazz songs", "jazz piano", "jazz classics"],
        "country": [f"top country songs {y}", "best country hits", "country music playlist"],
        "latin": [f"top latin hits {y}", "reggaeton hits", f"latin pop {y}", "bachata hits"],
        "indie": [f"best indie songs {y}", "indie rock playlist", "indie pop hits", "indie folk"],
        "bollywood": [f"latest bollywood songs {y}", "best hindi songs", "bollywood hits playlist"],
        "kpop": [f"top kpop songs {y}", "best kpop hits", "trending kpop", "kpop playlist"],
    }


def _mood_queries():
    y = _year()
    return {
        "happy": ["happy songs playlist", "feel good music", f"upbeat songs {y}", "cheerful music"],
        "sad": ["sad songs playlist", "emotional songs", "heartbreak songs", "melancholy music"],
        "energetic": ["workout music", "high energy songs", "pump up playlist", "gym music"],
        "chill": ["chill music playlist", "relaxing songs", "chill vibes", "lofi chill"],
        "romantic": ["romantic songs", "love songs playlist", "romance music", "couples playlist"],
        "focus": ["focus music", "study music", "concentration playlist", "deep focus"],
        "party": [f"party music {y}", "dance hits", "party playlist", "club music"],
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
    y = _year()
    queries = [
        f"trending songs {y}",
        "top hits this week",
        f"new music releases {y}",
        "popular songs right now",
    ]
    query = random.choice(queries)
    results = await search_songs(query, limit=limit)
    return results


async def get_for_you(uid: str, limit: int = 20) -> List[dict]:
    """Get 'For You' recommendations."""
    y = _year()
    queries = [
        f"recommended songs {y}",
        "songs you might like",
        f"discover new music {y}",
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
    y = _year()
    queries = [
        f"discover new artists {y}",
        "hidden gems music",
        f"underrated songs {y}",
        "new music friday",
    ]
    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_mood_recommendations(uid: str, mood: str, limit: int = 20) -> List[dict]:
    """Get mood-based recommendations."""
    mood_lower = mood.lower()
    queries = _mood_queries().get(mood_lower, [f"{mood} music playlist", f"{mood} songs"])
    query = random.choice(queries)
    return await search_songs(query, limit=limit)


async def get_by_type(category_type: str, language: str = "", limit: int = 20) -> List[dict]:
    """Get recommendations by genre/type."""
    type_lower = category_type.lower()
    queries = _genre_queries().get(type_lower, [f"{category_type} music playlist", f"best {category_type} songs"])

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


def _language_queries():
    y = _year()
    return {
        "hindi": [f"latest bollywood songs {y}", "best hindi songs", "new hindi songs", "hindi hits playlist"],
        "english": [f"top hits {y}", "best english songs", "trending english music", f"pop hits {y}"],
        "tamil": [f"latest tamil songs {y}", "best tamil songs", "tamil hits playlist", "new tamil music"],
        "telugu": [f"latest telugu songs {y}", "best telugu songs", "telugu hits playlist", "new telugu music"],
        "punjabi": [f"latest punjabi songs {y}", "best punjabi songs", "punjabi hits playlist", "new punjabi music"],
        "malayalam": [f"latest malayalam songs {y}", "best malayalam songs", "malayalam hits playlist"],
        "kannada": [f"latest kannada songs {y}", "best kannada songs", "kannada hits playlist"],
        "bengali": [f"latest bengali songs {y}", "best bengali songs", "bengali hits playlist"],
        "marathi": [f"latest marathi songs {y}", "best marathi songs", "marathi hits playlist"],
        "korean": [f"latest kpop songs {y}", "best korean songs", "trending kpop music", "kpop hits"],
        "spanish": [f"latest spanish songs {y}", "best spanish music", f"reggaeton hits {y}", "latin pop"],
    }

# Keep as static — no year needed
LANGUAGE_QUERIES = _language_queries  # Alias for recommend.py access

MOOD_EMOJI = {
    "happy": "😊", "sad": "😢", "romantic": "💕", "energetic": "⚡",
    "calm": "🧘", "party": "🎉", "workout": "💪", "focus": "🎯",
    "chill": "😎", "motivational": "🔥", "nostalgic": "🕰️", "devotional": "🙏",
}


async def get_language_mood_feed(language: str, moods: list, limit: int = 15) -> list:
    """
    Generate home feed sections based on user's language and mood preferences.
    Returns a list of sections: [{"title": "...", "songs": [...]}]
    """
    y = _year()
    sections = []
    lang = language.lower() if language else "english"

    # Section 1: Top songs in user's language
    lang_qs = _language_queries().get(lang, [f"top {lang} songs {y}", f"best {lang} music"])
    lang_query = random.choice(lang_qs)
    lang_songs = await search_songs(lang_query, limit=limit)
    lang_title = lang.title() if lang != "english" else "Global"
    sections.append({
        "title": f"🎵 Top {lang_title} Songs",
        "songs": lang_songs,
    })

    # Section 2-4: One section per mood (up to 3 moods)
    for mood in (moods or ["chill"])[:3]:
        mood_lower = mood.lower()
        emoji = MOOD_EMOJI.get(mood_lower, "🎶")

        # Combine mood + language for targeted results
        if lang != "english":
            mood_query = f"{mood_lower} {lang} songs {y}"
        else:
            mq = _mood_queries().get(mood_lower, [f"{mood_lower} music playlist"])
            mood_query = random.choice(mq)

        mood_songs = await search_songs(mood_query, limit=limit)
        sections.append({
            "title": f"{emoji} {mood.title()} {lang_title} Mix",
            "songs": mood_songs,
        })

    # Section 5: Trending (language-specific)
    if lang != "english":
        trending_query = f"trending {lang} songs {y}"
    else:
        trending_query = random.choice([f"trending songs {y}", f"viral songs {y}", "top hits this week"])
    trending_songs = await search_songs(trending_query, limit=limit)
    sections.append({
        "title": "🔥 Trending Now",
        "songs": trending_songs,
    })

    return sections


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

    return await search_songs(f"popular songs {_year()}", limit=limit)
