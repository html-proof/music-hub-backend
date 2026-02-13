"""
Firebase Music Database — Realtime Database manager.
Tracks everything: search, play, skip, complete.
Maintains keyword weights for personalized recommendations.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime
from uuid import uuid4
from enum import Enum

from firebase_admin import db as rtdb
from config.firebase_init import get_firestore_client
from services.keyword_extractor import KeywordExtractor

logger = logging.getLogger(__name__)


# ==================== ENUMS ====================

class Language(Enum):
    HINDI = "hindi"
    ENGLISH = "english"
    TAMIL = "tamil"
    TELUGU = "telugu"
    PUNJABI = "punjabi"
    MALAYALAM = "malayalam"
    KANNADA = "kannada"
    BENGALI = "bengali"
    MARATHI = "marathi"
    KOREAN = "korean"
    SPANISH = "spanish"


class Mood(Enum):
    HAPPY = "happy"
    SAD = "sad"
    ROMANTIC = "romantic"
    ENERGETIC = "energetic"
    CALM = "calm"
    PARTY = "party"
    WORKOUT = "workout"
    FOCUS = "focus"
    CHILL = "chill"
    MOTIVATIONAL = "motivational"
    NOSTALGIC = "nostalgic"
    DEVOTIONAL = "devotional"


class ActivityType(Enum):
    SEARCH = "search"
    PLAY = "play"
    SKIP = "skip"
    COMPLETE = "complete"
    PAUSE = "pause"
    LIKE = "like"
    DISLIKE = "dislike"


# ==================== RTDB REFERENCES ====================

def _ref(path: str):
    """Get a Realtime Database reference."""
    return rtdb.reference(path)


# ==================== DATABASE MANAGER ====================

class FirebaseMusicDatabase:
    """Firebase Realtime Database manager for all music tracking."""

    def __init__(self):
        self.keyword_extractor = KeywordExtractor()

    # ────────────────── USER OPS ──────────────────

    def create_user(self, user_id: str, language: str, moods: List[str]) -> bool:
        """Create new user with preferences."""
        try:
            user_data = {
                "user_id": user_id,
                "language": language,
                "moods": moods,
                "is_onboarded": True,
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat(),
                "total_searches": 0,
                "total_plays": 0,
                "total_skips": 0,
                "total_completes": 0,
            }
            _ref(f"/users/{user_id}").set(user_data)
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False

    def get_user(self, user_id: str) -> Optional[Dict]:
        try:
            return _ref(f"/users/{user_id}").get()
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def update_user_stats(self, user_id: str, stat_name: str, increment: int = 1):
        try:
            ref = _ref(f"/users/{user_id}")
            current = ref.child(stat_name).get() or 0
            ref.update({
                stat_name: current + increment,
                "updated_at": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error updating stats: {e}")

    def is_user_onboarded(self, user_id: str) -> bool:
        user = self.get_user(user_id)
        return user is not None and user.get("is_onboarded", False)

    # ────────────────── SEARCH TRACKING ──────────────────

    def track_search(self, user_id: str, search_query: str,
                     results_count: int, clicked_result: Optional[str] = None) -> str:
        """Track search activity. Returns search_id."""
        try:
            user = self.get_user(user_id)
            language = user.get("language", "english") if user else "english"

            keywords = self.keyword_extractor.extract_keywords(search_query, language)

            search_data = {
                "user_id": user_id,
                "search_query": search_query,
                "keywords": keywords,
                "searched_at": datetime.utcnow().isoformat(),
                "results_count": results_count,
                "clicked_result": clicked_result,
                "language": language,
            }

            search_id = str(uuid4())
            _ref(f"/search_history/{user_id}/{search_id}").set(search_data)

            # Update keyword weights
            self._update_user_keywords(user_id, keywords, weight=1.0, context="search")
            self.update_user_stats(user_id, "total_searches")

            return search_id
        except Exception as e:
            logger.error(f"Error tracking search: {e}")
            return ""

    def get_user_searches(self, user_id: str, limit: int = 50) -> List[Dict]:
        try:
            searches = _ref(f"/search_history/{user_id}").order_by_child(
                "searched_at"
            ).limit_to_last(limit).get()
            if not searches:
                return []

            result = []
            for sid, data in searches.items():
                data["search_id"] = sid
                result.append(data)
            result.sort(key=lambda x: x["searched_at"], reverse=True)
            return result
        except Exception as e:
            logger.error(f"Error getting searches: {e}")
            return []

    # ────────────────── PLAY / SKIP / COMPLETE ──────────────────

    def track_play(self, user_id: str, video_id: str, title: str,
                   artist: str, channel: str, duration: int) -> str:
        """Track when user starts playing a song. Returns play_id."""
        try:
            user = self.get_user(user_id)
            language = user.get("language", "english") if user else "english"

            kw = self.keyword_extractor.extract_from_song_data(title, artist, language)

            play_data = {
                "user_id": user_id,
                "video_id": video_id,
                "title": title,
                "artist": artist,
                "channel": channel,
                "duration": duration,
                "played_at": datetime.utcnow().isoformat(),
                "language": language,
                "keywords": kw["all_keywords"],
                "title_keywords": kw["title_keywords"],
                "artist_keywords": kw["artist_keywords"],
                "status": "playing",
                "play_duration": 0,
                "completion_percentage": 0.0,
            }

            play_id = str(uuid4())
            _ref(f"/play_history/{user_id}/{play_id}").set(play_data)

            self._update_user_keywords(user_id, kw["all_keywords"], weight=0.5, context="play_start")
            self.update_user_stats(user_id, "total_plays")
            self._log_activity(user_id, ActivityType.PLAY.value, {
                "video_id": video_id, "title": title, "artist": artist,
            })
            return play_id
        except Exception as e:
            logger.error(f"Error tracking play: {e}")
            return ""

    def track_skip(self, user_id: str, play_id: str, play_duration: int):
        """Track skip — reduces keyword weight if skipped early (<20%)."""
        try:
            ref = _ref(f"/play_history/{user_id}/{play_id}")
            play_data = ref.get()
            if not play_data:
                return

            total = play_data.get("duration", 1)
            pct = (play_duration / total) * 100 if total > 0 else 0

            ref.update({
                "status": "skipped",
                "play_duration": play_duration,
                "completion_percentage": pct,
                "skipped_at": datetime.utcnow().isoformat(),
            })

            # Early skip = negative signal
            if pct < 20:
                self._update_user_keywords(
                    user_id, play_data.get("keywords", []),
                    weight=-2.0, context="skip_early",
                )

            self.update_user_stats(user_id, "total_skips")
            self._log_activity(user_id, ActivityType.SKIP.value, {
                "play_id": play_id,
                "video_id": play_data.get("video_id"),
                "completion_percentage": pct,
            })
        except Exception as e:
            logger.error(f"Error tracking skip: {e}")

    def track_complete(self, user_id: str, play_id: str, play_duration: int):
        """Track completion — heavily boosts keyword weight (+5/+8 for artist)."""
        try:
            ref = _ref(f"/play_history/{user_id}/{play_id}")
            play_data = ref.get()
            if not play_data:
                return

            total = play_data.get("duration", 1)
            pct = (play_duration / total) * 100 if total > 0 else 0

            ref.update({
                "status": "completed",
                "play_duration": play_duration,
                "completion_percentage": pct,
                "completed_at": datetime.utcnow().isoformat(),
            })

            keywords = play_data.get("keywords", [])
            artist_kw = play_data.get("artist_keywords", [])

            self._update_user_keywords(user_id, keywords, weight=5.0, context="complete")
            self._update_user_keywords(user_id, artist_kw, weight=8.0, context="complete_artist")
            self.update_user_stats(user_id, "total_completes")

            self._log_activity(user_id, ActivityType.COMPLETE.value, {
                "play_id": play_id,
                "video_id": play_data.get("video_id"),
                "title": play_data.get("title"),
                "artist": play_data.get("artist"),
            })
        except Exception as e:
            logger.error(f"Error tracking complete: {e}")

    def get_play_history(self, user_id: str, limit: int = 100) -> List[Dict]:
        try:
            plays = _ref(f"/play_history/{user_id}").order_by_child(
                "played_at"
            ).limit_to_last(limit).get()
            if not plays:
                return []
            result = []
            for pid, data in plays.items():
                data["play_id"] = pid
                result.append(data)
            result.sort(key=lambda x: x["played_at"], reverse=True)
            return result
        except Exception as e:
            logger.error(f"Error getting play history: {e}")
            return []

    # ────────────────── KEYWORD WEIGHT MANAGEMENT ──────────────────

    def _update_user_keywords(self, user_id: str, keywords: List[str],
                              weight: float, context: str):
        """Update keyword weights — the core of personalized recommendations."""
        try:
            for keyword in keywords:
                if not keyword:
                    continue
                # Firebase RTDB keys can't contain . # $ [ ] /
                safe_key = keyword.replace(".", "_").replace("#", "_").replace(
                    "$", "_").replace("[", "_").replace("]", "_").replace("/", "_")

                ref = _ref(f"/user_keywords/{user_id}/{safe_key}")
                current = ref.get() or {"weight": 0.0, "count": 0, "contexts": {}}

                contexts = current.get("contexts", {})
                contexts[context] = contexts.get(context, 0) + 1

                ref.update({
                    "weight": current["weight"] + weight,
                    "count": current["count"] + 1,
                    "contexts": contexts,
                    "last_updated": datetime.utcnow().isoformat(),
                })
        except Exception as e:
            logger.error(f"Error updating keywords: {e}")

    def get_user_top_keywords(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's top keywords sorted by weight — core of recommendations."""
        try:
            keywords = _ref(f"/user_keywords/{user_id}").get()
            if not keywords:
                return []

            kw_list = []
            for keyword, data in keywords.items():
                kw_list.append({
                    "keyword": keyword,
                    "weight": data.get("weight", 0),
                    "count": data.get("count", 0),
                    "contexts": data.get("contexts", {}),
                })
            kw_list.sort(key=lambda x: x["weight"], reverse=True)
            return kw_list[:limit]
        except Exception as e:
            logger.error(f"Error getting top keywords: {e}")
            return []

    # ────────────────── ACTIVITY LOG ──────────────────

    def _log_activity(self, user_id: str, activity_type: str, data: Dict):
        try:
            aid = str(uuid4())
            _ref(f"/activity_log/{user_id}/{aid}").set({
                "user_id": user_id,
                "activity_type": activity_type,
                "data": data,
                "timestamp": datetime.utcnow().isoformat(),
            })
        except Exception as e:
            logger.error(f"Error logging activity: {e}")

    def get_user_activity_log(self, user_id: str, limit: int = 100) -> List[Dict]:
        try:
            activities = _ref(f"/activity_log/{user_id}").order_by_child(
                "timestamp"
            ).limit_to_last(limit).get()
            if not activities:
                return []
            result = []
            for aid, data in activities.items():
                data["activity_id"] = aid
                result.append(data)
            result.sort(key=lambda x: x["timestamp"], reverse=True)
            return result
        except Exception as e:
            logger.error(f"Error getting activity log: {e}")
            return []


# Singleton
music_db = FirebaseMusicDatabase()
