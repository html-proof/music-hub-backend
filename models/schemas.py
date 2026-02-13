from pydantic import BaseModel
from typing import List, Optional, Any


# ============================================================================
# Song Models
# ============================================================================

class SongResponse(BaseModel):
    id: str
    title: str
    artist: str
    thumbnailUrl: str = ""
    audioUrl: str = ""
    durationSeconds: int = 0


# ============================================================================
# Auth Models
# ============================================================================

class GoogleSignInRequest(BaseModel):
    """Google Sign-In request with Firebase token"""
    firebase_token: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    display_name: str = ""


class LoginRequest(BaseModel):
    id_token: str


class LoginResponse(BaseModel):
    user: dict
    onboarding_required: bool = True
    has_preferences: bool = False


# ============================================================================
# Music Models
# ============================================================================

class PlayRequest(BaseModel):
    id: Optional[str] = None
    videoId: Optional[str] = None
    quality: str = "high"


class PlayResponse(BaseModel):
    success: bool = True
    data: dict = {}


class SearchResponse(BaseModel):
    results: List[SongResponse] = []


class PrefetchRequest(BaseModel):
    ids: List[str] = []
    quality: str = "high"


# ============================================================================
# Playlist Models
# ============================================================================

class PlaylistCreateRequest(BaseModel):
    name: str


class PlaylistAddSongRequest(BaseModel):
    song_id: str


class PlaylistResponse(BaseModel):
    id: str
    name: str
    songs: List[SongResponse] = []


# ============================================================================
# User Models
# ============================================================================

class OnboardingRequest(BaseModel):
    language: str = ""
    moods: List[str] = []
    genres: List[str] = []


class PreferencesResponse(BaseModel):
    selectedLanguage: str = ""
    selectedMoods: List[str] = []
    favoriteGenres: List[str] = []


class LikeRequest(BaseModel):
    song_id: str
    title: str = ""
    artist: str = ""
    thumbnailUrl: str = ""
    audioUrl: str = ""
    durationSeconds: int = 0


# ============================================================================
# Recommendation Models
# ============================================================================

class RecommendationResponse(BaseModel):
    success: bool = True
    data: List[SongResponse] = []


# ============================================================================
# Smart Recommendation Models
# ============================================================================

class TimeContextResponse(BaseModel):
    year: int
    month: str
    month_num: int
    day: int
    weekday: str
    time_of_day: str
    is_weekend: bool
    season: str


class SmartRecommendationResponseModel(BaseModel):
    success: bool = True
    recommendations: List[SongResponse] = []
    count: int = 0
    quality_level: str = "medium_quality"
    context: TimeContextResponse


class SmartFeedResponseModel(BaseModel):
    success: bool = True
    songs: List[SongResponse] = []
    page: int = 1
    page_size: int = 20
    total: int = 0
    has_more: bool = False
    context: TimeContextResponse


class QualityStatsResponse(BaseModel):
    quality_levels: dict = {}
    trusted_channels: dict = {}
