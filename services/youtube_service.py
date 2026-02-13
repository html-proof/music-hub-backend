"""
YouTube Service — yt-dlp based search & audio extraction.
Handles searching YouTube for songs and resolving audio-only stream URLs.
"""

import asyncio
import time
import re
from typing import Optional, List, Dict
from cachetools import TTLCache


# In-memory cache for resolved stream URLs (5 min TTL)
_url_cache: TTLCache = TTLCache(maxsize=500, ttl=300)

# In-memory cache for search results (2 min TTL)
_search_cache: TTLCache = TTLCache(maxsize=100, ttl=120)

# Hit/miss counters
_cache_stats = {"search_hits": 0, "search_misses": 0, "stream_hits": 0, "stream_misses": 0}


def _run_yt_dlp_extract(video_id: str, quality: str = "high") -> Optional[dict]:
    """Synchronous yt-dlp extraction — runs in thread pool."""
    import yt_dlp

    quality_formats = {
        "high": "bestaudio[ext=m4a]/bestaudio/best",
        "medium": "bestaudio[abr<=128]/bestaudio/best",
        "low": "bestaudio[abr<=64]/worstaudio/best",
        "48k": "bestaudio[abr<=48]/worstaudio/best",
        "64k": "bestaudio[abr<=64]/worstaudio/best",
    }

    fmt = quality_formats.get(quality, quality_formats["high"])

    opts = {
        "format": fmt,
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,
        "skip_download": True,
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            url = f"https://www.youtube.com/watch?v={video_id}"
            info = ydl.extract_info(url, download=False)

            if not info:
                return None

            stream_url = info.get("url")
            if not stream_url:
                # Try formats list
                formats = info.get("formats", [])
                audio_formats = [f for f in formats if f.get("acodec") != "none" and f.get("vcodec") in ("none", None)]
                if audio_formats:
                    stream_url = audio_formats[-1].get("url")
                elif formats:
                    stream_url = formats[-1].get("url")

            return {
                "stream_url": stream_url,
                "title": info.get("title", ""),
                "artist": info.get("uploader", info.get("channel", "Unknown")),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "view_count": info.get("view_count", 0),
            }
    except Exception as e:
        print(f"❌ yt-dlp extract error for {video_id}: {e}")
        return None


def _run_yt_dlp_search(query: str, limit: int = 10) -> List[dict]:
    """Synchronous yt-dlp search — runs in thread pool."""
    import yt_dlp

    opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "default_search": f"ytsearch{limit}",
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
            entries = result.get("entries", []) if result else []

            songs = []
            for entry in entries:
                if not entry:
                    continue

                video_id = entry.get("id", "")
                title = entry.get("title", "")
                uploader = entry.get("uploader", entry.get("channel", "Unknown"))
                duration = entry.get("duration") or 0
                thumbnail = entry.get("thumbnail", entry.get("thumbnails", [{}])[0].get("url", "") if entry.get("thumbnails") else "")

                if not video_id or not title:
                    continue

                # Generate thumbnail if missing
                if not thumbnail:
                    thumbnail = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"

                # Clean up artist name
                artist = _clean_artist_name(uploader, title)

                songs.append({
                    "id": video_id,
                    "title": _clean_title(title),
                    "artist": artist,
                    "thumbnailUrl": thumbnail,
                    "audioUrl": "",
                    "durationSeconds": int(duration) if duration else 0,
                })

            return songs
    except Exception as e:
        print(f"❌ yt-dlp search error: {e}")
        return []


def _clean_title(title: str) -> str:
    """Clean up YouTube video title for display."""
    # Remove common suffixes
    patterns = [
        r'\s*\(Official\s*(Music\s*)?Video\)',
        r'\s*\[Official\s*(Music\s*)?Video\]',
        r'\s*\(Official\s*Audio\)',
        r'\s*\[Official\s*Audio\]',
        r'\s*\(Lyrics?\)',
        r'\s*\[Lyrics?\]',
        r'\s*\|\s*Official\s*(Music\s*)?Video',
        r'\s*\(HD\)',
        r'\s*\[HD\]',
        r'\s*\(HQ\)',
    ]
    result = title
    for pattern in patterns:
        result = re.sub(pattern, '', result, flags=re.IGNORECASE)
    return result.strip()


def _clean_artist_name(uploader: str, title: str) -> str:
    """Extract artist name from uploader or title."""
    # Remove common channel suffixes
    artist = uploader
    for suffix in [" - Topic", "VEVO", " Official", " Music"]:
        artist = artist.replace(suffix, "")

    # If title has "Artist - Song" format, prefer that
    if " - " in title:
        parts = title.split(" - ", 1)
        if len(parts) == 2 and len(parts[0].strip()) > 1:
            artist = parts[0].strip()

    return artist.strip()


async def search_songs(query: str, limit: int = 10) -> List[dict]:
    """Search YouTube for songs."""
    cache_key = f"search:{query}:{limit}"
    if cache_key in _search_cache:
        _cache_stats["search_hits"] += 1
        print(f"🔥 Search cache HIT: {query}")
        return _search_cache[cache_key]

    _cache_stats["search_misses"] += 1
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _run_yt_dlp_search, query, limit)

    if results:
        _search_cache[cache_key] = results

    return results


async def get_stream_url(video_id: str, quality: str = "high") -> Optional[dict]:
    """Get audio stream URL for a YouTube video."""
    cache_key = f"stream:{video_id}:{quality}"
    if cache_key in _url_cache:
        _cache_stats["stream_hits"] += 1
        print(f"🔥 Stream cache HIT: {video_id}")
        return _url_cache[cache_key]

    _cache_stats["stream_misses"] += 1
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, _run_yt_dlp_extract, video_id, quality)

    if result and result.get("stream_url"):
        _url_cache[cache_key] = result

    return result


async def prefetch_songs(video_ids: List[str], quality: str = "high"):
    """Prefetch stream URLs for a list of video IDs (fire-and-forget)."""
    for vid in video_ids[:5]:  # Limit to 5
        try:
            await get_stream_url(vid, quality)
        except Exception as e:
            print(f"⚠️ Prefetch error for {vid}: {e}")


def get_cache_stats() -> dict:
    """Return cache statistics."""
    total_search = _cache_stats["search_hits"] + _cache_stats["search_misses"]
    total_stream = _cache_stats["stream_hits"] + _cache_stats["stream_misses"]
    return {
        "search_cache": {
            "size": len(_search_cache),
            "max_size": _search_cache.maxsize,
            "ttl_seconds": int(_search_cache.ttl),
            "hits": _cache_stats["search_hits"],
            "misses": _cache_stats["search_misses"],
            "hit_rate": round(_cache_stats["search_hits"] / total_search * 100, 1) if total_search else 0,
        },
        "stream_cache": {
            "size": len(_url_cache),
            "max_size": _url_cache.maxsize,
            "ttl_seconds": int(_url_cache.ttl),
            "hits": _cache_stats["stream_hits"],
            "misses": _cache_stats["stream_misses"],
            "hit_rate": round(_cache_stats["stream_hits"] / total_stream * 100, 1) if total_stream else 0,
        },
        "total_requests": total_search + total_stream,
        "total_hit_rate": round(
            (_cache_stats["search_hits"] + _cache_stats["stream_hits"])
            / (total_search + total_stream) * 100, 1
        ) if (total_search + total_stream) else 0,
    }


def clear_caches():
    """Clear all caches and reset counters."""
    _search_cache.clear()
    _url_cache.clear()
    _cache_stats["search_hits"] = 0
    _cache_stats["search_misses"] = 0
    _cache_stats["stream_hits"] = 0
    _cache_stats["stream_misses"] = 0
    return {"status": "cleared", "message": "All caches cleared"}
