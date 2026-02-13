"""
Smart Recommendation Engine — based purely on stored Firebase data.
Uses keyword weights, play history, search history to generate recommendations.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from collections import Counter

from services.firebase_db import FirebaseMusicDatabase, music_db, Language, Mood

logger = logging.getLogger(__name__)


class SmartRecommendationEngine:
    """Generates personalized recommendations from keyword weights and history."""

    def __init__(self, db: FirebaseMusicDatabase):
        self.db = db

    # ────────────────── MAIN ENTRY ──────────────────

    def generate_recommendations(self, user_id: str, limit: int = 30) -> List[Dict]:
        """Generate personalized recommendations from all stored data."""
        user = self.db.get_user(user_id)
        if not user:
            return self._get_default_recommendations(limit)

        language = user.get("language", "english")
        moods = user.get("moods", [])

        recs: List[Dict] = []

        # 40% — keyword-based
        recs.extend(self._keyword_based(user_id, language, limit=15))
        # 30% — artist-based
        recs.extend(self._artist_based(user_id, language, limit=10))
        # 20% — mood-based
        recs.extend(self._mood_based(user_id, moods, language, limit=8))
        # 10% — similar to completed
        recs.extend(self._similar_to_completed(user_id, language, limit=7))

        unique = self._deduplicate_and_score(recs)
        unique.sort(key=lambda x: x["score"], reverse=True)
        return unique[:limit]

    # ────────────────── KEYWORD-BASED (40%) ──────────────────

    def _keyword_based(self, user_id: str, language: str, limit: int) -> List[Dict]:
        recs = []
        top_keywords = self.db.get_user_top_keywords(user_id, limit=20)

        for kw in top_keywords[:10]:
            keyword = kw["keyword"]
            weight = kw["weight"]

            for query in [
                f"{keyword} {language} songs",
                f"{keyword} music {language}",
                f"best {keyword} songs",
                f"{keyword} latest",
            ]:
                recs.append({
                    "query": query,
                    "type": "keyword_based",
                    "source_keyword": keyword,
                    "keyword_weight": weight,
                    "language": language,
                    "score": weight * 0.4,
                    "priority": "high",
                })
        return recs

    # ────────────────── ARTIST-BASED (30%) ──────────────────

    def _artist_based(self, user_id: str, language: str, limit: int) -> List[Dict]:
        recs = []
        history = self.db.get_play_history(user_id, limit=100)

        artist_counts: Counter = Counter()
        for play in history:
            if play.get("status") == "completed":
                artist = play.get("artist", "").lower().strip()
                if artist:
                    artist_counts[artist] += 1

        for artist, count in artist_counts.most_common(5):
            for query in [
                f"{artist} all songs",
                f"{artist} latest songs {language}",
                f"{artist} best hits",
                f"{artist} new song",
            ]:
                recs.append({
                    "query": query,
                    "type": "artist_based",
                    "artist": artist,
                    "play_count": count,
                    "language": language,
                    "score": count * 0.3,
                    "priority": "high",
                })
        return recs

    # ────────────────── MOOD-BASED (20%) ──────────────────

    MOOD_KEYWORDS = {
        "happy": ["happy", "cheerful", "upbeat", "joyful"],
        "sad": ["sad", "emotional", "heartbreak"],
        "romantic": ["romantic", "love", "pyaar"],
        "energetic": ["energetic", "dance", "party"],
        "calm": ["calm", "peaceful", "relaxing"],
        "party": ["party", "club", "dj"],
        "workout": ["workout", "gym", "motivation"],
        "focus": ["focus", "study", "concentration", "ambient"],
        "chill": ["chill", "lofi", "relax"],
        "motivational": ["motivational", "inspirational", "power"],
        "nostalgic": ["nostalgic", "old", "retro", "classic"],
        "devotional": ["devotional", "bhajan", "spiritual"],
    }

    def _mood_based(self, user_id: str, moods: List[str],
                    language: str, limit: int) -> List[Dict]:
        recs = []
        for mood in moods:
            keywords = self.MOOD_KEYWORDS.get(mood.lower(), [mood])
            for kw in keywords[:2]:
                recs.append({
                    "query": f"{kw} {language} songs",
                    "type": "mood_based",
                    "mood": mood,
                    "language": language,
                    "score": 2.0,
                    "priority": "medium",
                })
        return recs

    # ────────────────── SIMILAR TO COMPLETED (10%) ──────────────────

    def _similar_to_completed(self, user_id: str, language: str,
                              limit: int) -> List[Dict]:
        recs = []
        history = self.db.get_play_history(user_id, limit=50)
        completed = [p for p in history if p.get("status") == "completed"]

        all_kw: List[str] = []
        for play in completed[:10]:
            all_kw.extend(play.get("keywords", []))

        freq = Counter(all_kw)
        for keyword, count in freq.most_common(5):
            recs.append({
                "query": f"songs like {keyword}",
                "type": "similar_to_completed",
                "keyword": keyword,
                "frequency": count,
                "language": language,
                "score": count * 0.1,
                "priority": "low",
            })
        return recs

    # ────────────────── HELPERS ──────────────────

    def _deduplicate_and_score(self, recs: List[Dict]) -> List[Dict]:
        unique: Dict[str, Dict] = {}
        for rec in recs:
            key = rec["query"].lower()
            if key not in unique:
                unique[key] = rec
            else:
                unique[key]["score"] += rec["score"]
        return list(unique.values())

    def _get_default_recommendations(self, limit: int) -> List[Dict]:
        return [
            {"query": "trending songs 2024", "type": "default", "score": 1.0, "priority": "low"},
            {"query": "top hits 2024", "type": "default", "score": 1.0, "priority": "low"},
            {"query": "popular music", "type": "default", "score": 1.0, "priority": "low"},
        ][:limit]

    # ────────────────── SEARCH SUGGESTIONS ──────────────────

    def get_search_suggestions(self, user_id: str, partial_query: str,
                               limit: int = 10) -> List[str]:
        """Autocomplete suggestions based on user's keywords and history."""
        suggestions: List[str] = []
        partial = partial_query.lower()

        # From keywords
        top_kw = self.db.get_user_top_keywords(user_id, limit=20)
        for kw in top_kw:
            keyword = kw["keyword"]
            if partial in keyword.lower() or keyword.lower().startswith(partial):
                suggestions.append(keyword)

        # From recent searches
        searches = self.db.get_user_searches(user_id, limit=20)
        for s in searches:
            q = s.get("search_query", "")
            if partial in q.lower() and q not in suggestions:
                suggestions.append(q)

        return suggestions[:limit]

    # ────────────────── CACHING ──────────────────

    def cache_recommendations(self, user_id: str) -> bool:
        """Cache recommendations in RTDB for faster loads."""
        try:
            from firebase_admin import db as rtdb
            recs = self.generate_recommendations(user_id, limit=50)
            rtdb.reference(f"/recommendations_cache/{user_id}").set({
                "user_id": user_id,
                "recommendations": recs,
                "generated_at": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=6)).isoformat(),
            })
            return True
        except Exception as e:
            logger.error(f"Error caching recommendations: {e}")
            return False

    def get_cached_recommendations(self, user_id: str) -> Optional[List[Dict]]:
        """Get cached recs if not expired."""
        try:
            from firebase_admin import db as rtdb
            cache = rtdb.reference(f"/recommendations_cache/{user_id}").get()
            if not cache:
                return None
            expires = datetime.fromisoformat(cache["expires_at"])
            if datetime.utcnow() > expires:
                return None
            return cache.get("recommendations", [])
        except Exception as e:
            logger.error(f"Error getting cached recs: {e}")
            return None


# Singleton
smart_engine = SmartRecommendationEngine(music_db)
