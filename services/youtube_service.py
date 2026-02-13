"""
YouTube Service — yt-dlp based search & audio extraction.
Handles searching YouTube for songs and resolving audio-only stream URLs.
"""

import asyncio
import os
import time
import re
import tempfile
from typing import Optional, List, Dict
from cachetools import TTLCache


# In-memory cache for resolved stream URLs (30 min TTL — YouTube URLs valid ~6hrs)
_url_cache: TTLCache = TTLCache(maxsize=2000, ttl=1800)

# In-memory cache for search results (10 min TTL)
_search_cache: TTLCache = TTLCache(maxsize=500, ttl=600)

# Hit/miss counters
_cache_stats = {"search_hits": 0, "search_misses": 0, "stream_hits": 0, "stream_misses": 0}

# Cookie file path (resolved once)
_cookie_file_path: Optional[str] = None


def _get_cookie_path() -> Optional[str]:
    """Get path to YouTube cookies file. Reads from YOUTUBE_COOKIES env var."""
    global _cookie_file_path

    if _cookie_file_path and os.path.exists(_cookie_file_path):
        return _cookie_file_path

    cookies_content = os.environ.get("YOUTUBE_COOKIES", "").strip()
    if not cookies_content:
        return None

    try:
        # Ensure Netscape header is present (yt-dlp requires it)
        if not cookies_content.startswith("# Netscape HTTP Cookie File") and \
           not cookies_content.startswith("# HTTP Cookie File"):
            cookies_content = "# Netscape HTTP Cookie File\n# This file is generated automatically.\n\n" + cookies_content

        # Basic validation — must have at least one tab-separated cookie line
        has_cookie = any(
            line.strip() and not line.startswith("#") and "\t" in line
            for line in cookies_content.split("\n")
        )
        if not has_cookie:
            print("⚠️ YOUTUBE_COOKIES env var set but contains no valid cookie lines — ignoring")
            return None

        # Write cookies to a temp file
        cookie_path = os.path.join(tempfile.gettempdir(), "yt_cookies.txt")
        with open(cookie_path, "w", encoding="utf-8") as f:
            f.write(cookies_content)
        _cookie_file_path = cookie_path
        print(f"✅ YouTube cookies loaded ({len(cookies_content)} bytes)")
        return cookie_path
    except Exception as e:
        print(f"❌ Error writing cookie file: {e}")
        return None


def _base_opts() -> dict:
    """Common yt-dlp options with cookie + header support."""
    opts = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "http_headers": {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
        },
    }

    cookie_path = _get_cookie_path()
    if cookie_path:
        opts["cookiefile"] = cookie_path

    return opts


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
        **_base_opts(),
        "format": fmt,
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

    # Sanitize query first
    clean_query = _sanitize_query(query)

    # Request extra results to compensate for filtered items
    fetch_limit = min(limit + 10, 30)

    opts = {
        **_base_opts(),
        "extract_flat": True,
        "skip_download": True,
        "default_search": f"ytsearch{fetch_limit}",
    }

    try:
        with yt_dlp.YoutubeDL(opts) as ydl:
            result = ydl.extract_info(f"ytsearch{fetch_limit}:{clean_query}", download=False)
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

                # Block inappropriate / non-music content
                if _is_blocked_content(title):
                    continue

                # Skip songs longer than 10 minutes (likely compilations/albums)
                if duration and int(duration) > 600:
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

                if len(songs) >= limit:
                    break

            return songs
    except Exception as e:
        print(f"❌ yt-dlp search error: {e}")
        return []


# ==================== CONTENT FILTER ====================

# Keywords that indicate non-music content — block these from results
_BLOCKED_TITLE_KEYWORDS = [
    # Non-music content
    "movie scene", "movie clip", "movie scenes", "movie sences", "film scene",
    "movie cut", "best scenes", "comedy scene", "fight scene", "action scene",
    "bgm", "background music", "background score",
    "3d audio", "8d audio", "16d audio", "3d song", "8d song",
    "trailer", "teaser", "behind the scenes",
    "interview", "making of", "reaction", "review",
    "dialogue", "dialogues", "movie dialogue",
    # Inappropriate content
    "porn", "xxx", "nudity", "nude", "naked", "sex scene",
    "adult video", "18+", "erotic", "explicit scene",
    "hot scene", "kissing scene", "intimate scene", "bed scene",
    "bold scene", "uncensored",
    # Non-music types
    "asmr", "podcast", "audiobook", "full movie", "full film",
    "short film", "web series", "tv series",
    "gameplay", "gaming", "walkthrough",
    "news channel", "news report", "breaking news",
    "speech", "lecture", "tutorial",
]

# Compiled regex for fast matching
_BLOCKED_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(kw) for kw in _BLOCKED_TITLE_KEYWORDS) + r')\b',
    re.IGNORECASE
)

# Keywords to strip from search queries
_QUERY_BLOCK_WORDS = [
    "porn", "xxx", "nudity", "nude", "naked", "sex",
    "adult", "18+", "erotic", "explicit", "uncensored",
    "hot scene", "kissing scene", "intimate", "bed scene",
    "bold scene",
]

_QUERY_BLOCK_PATTERN = re.compile(
    r'\b(?:' + '|'.join(re.escape(w) for w in _QUERY_BLOCK_WORDS) + r')\b',
    re.IGNORECASE
)


def _is_blocked_content(title: str) -> bool:
    """Check if a video title contains blocked keywords."""
    return bool(_BLOCKED_PATTERN.search(title))


def _sanitize_query(query: str) -> str:
    """Remove inappropriate keywords from search query."""
    cleaned = _QUERY_BLOCK_PATTERN.sub('', query)
    # Collapse extra spaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned if cleaned else "music"


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
    """Search YouTube for songs — auto-prefetches top results for instant play."""
    cache_key = f"search:{query}:{limit}"
    if cache_key in _search_cache:
        _cache_stats["search_hits"] += 1
        return _search_cache[cache_key]

    _cache_stats["search_misses"] += 1
    loop = asyncio.get_event_loop()
    results = await loop.run_in_executor(None, _run_yt_dlp_search, query, limit)

    if results:
        _search_cache[cache_key] = results
        # Auto-prefetch top 5 results in background for instant playback
        top_ids = [r["id"] for r in results[:5] if r.get("id")]
        if top_ids:
            asyncio.create_task(_background_prefetch(top_ids))

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


async def _background_prefetch(video_ids: List[str], quality: str = "high"):
    """Concurrently prefetch stream URLs — fires after search to warm cache."""
    try:
        tasks = [get_stream_url(vid, quality) for vid in video_ids[:5]]
        await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        pass  # Fire-and-forget, never crash


async def prefetch_songs(video_ids: List[str], quality: str = "high"):
    """Prefetch stream URLs for a list of video IDs (fire-and-forget)."""
    await _background_prefetch(video_ids, quality)


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
