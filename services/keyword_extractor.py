"""
Keyword Extractor — Extract meaningful keywords from search queries, song titles, artists.
Core of the recommendation system.
"""

import re
from typing import List, Dict, Set


class KeywordExtractor:
    """Extract meaningful keywords from text for recommendation weighting."""

    # Stop words to ignore (per language)
    STOP_WORDS = {
        "english": {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "from", "song", "music", "video", "audio", "official",
            "lyrics", "full", "new", "latest", "best", "top","epic","shorts","remix","cover","remix","Sun nxt","prime""
        },
        "hindi": {
            "ka", "ke", "ki", "se", "ne", "ko", "mein", "hai", "tha", "thi", "the",
            "song", "gana", "gaana", "music", "video",
        },
        "tamil": {"song", "paadal", "music", "video"},
        "telugu": {"song", "paata", "music", "video"},
    }

    # Music terms that should always be kept
    MUSIC_TERMS = {
        "remix", "unplugged", "acoustic", "live", "version", "cover",
        "mashup", "lofi", "slowed", "reverb", "dj", "edm", "rock",
        "pop", "rap", "hip hop", "classical", "jazz", "blues",
    }

    def extract_keywords(self, text: str, language: str = "english",
                         min_length: int = 2) -> List[str]:
        """Extract keywords from text, sorted by importance."""
        if not text:
            return []

        text = text.lower().strip()
        text = re.sub(r"[^\w\s\-]", " ", text)
        words = text.split()

        stop_words = self.STOP_WORDS.get(language, self.STOP_WORDS["english"])

        keywords = []
        for word in words:
            word = word.strip("-").strip()
            if len(word) < min_length:
                continue
            if word in stop_words and word not in self.MUSIC_TERMS:
                continue
            if word.isdigit():
                continue
            keywords.append(word)

        # Also extract bigrams
        bigrams = self._extract_bigrams(text, stop_words)
        keywords.extend(bigrams)

        # Deduplicate preserving order
        seen: Set[str] = set()
        unique = []
        for kw in keywords:
            if kw not in seen:
                seen.add(kw)
                unique.append(kw)

        return unique

    def _extract_bigrams(self, text: str, stop_words: Set[str]) -> List[str]:
        """Extract two-word phrases."""
        words = text.split()
        bigrams = []
        for i in range(len(words) - 1):
            w1, w2 = words[i].strip(), words[i + 1].strip()
            if w1 in stop_words and w2 in stop_words:
                continue
            if len(w1) < 2 or len(w2) < 2:
                continue
            bigrams.append(f"{w1} {w2}")
        return bigrams

    def extract_from_song_data(self, title: str, artist: str,
                               language: str) -> Dict[str, List[str]]:
        """Extract categorized keywords from song title and artist."""
        title_keywords = self.extract_keywords(title, language)
        artist_keywords = self.extract_keywords(artist, language)
        return {
            "title_keywords": title_keywords,
            "artist_keywords": artist_keywords,
            "all_keywords": list(set(title_keywords + artist_keywords)),
        }
