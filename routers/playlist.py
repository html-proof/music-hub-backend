"""
Playlist Router — create, add songs, list playlists via Firestore.
"""

from fastapi import APIRouter, Depends, HTTPException
from typing import Optional
from models.schemas import PlaylistCreateRequest, PlaylistAddSongRequest
from middleware.auth import get_current_user, get_optional_user
from config.firebase_init import get_firestore_client
import datetime

router = APIRouter(prefix="/playlist", tags=["playlists"])


@router.get("/my")
async def get_my_playlists(user: Optional[dict] = Depends(get_optional_user)):
    """Get the current user's playlists."""
    if not user:
        return {"playlists": []}

    uid = user["uid"]
    db = get_firestore_client()

    if not db:
        return {"playlists": []}

    try:
        playlists_ref = db.collection("users").document(uid).collection("playlists")
        docs = playlists_ref.order_by("createdAt", direction="DESCENDING").stream()

        playlists = []
        for doc in docs:
            data = doc.to_dict()
            playlists.append({
                "id": doc.id,
                "name": data.get("name", ""),
                "songs": data.get("songs", []),
            })

        return {"playlists": playlists}
    except Exception as e:
        print(f"❌ Error getting playlists: {e}")
        return {"playlists": []}


@router.post("/create")
async def create_playlist(request: PlaylistCreateRequest, user: dict = Depends(get_current_user)):
    """Create a new playlist."""
    uid = user["uid"]
    db = get_firestore_client()

    if not db:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        playlist_ref = db.collection("users").document(uid).collection("playlists").document()
        playlist_ref.set({
            "name": request.name,
            "songs": [],
            "createdAt": datetime.datetime.now(),
        })

        return {
            "success": True,
            "id": playlist_ref.id,
            "name": request.name,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating playlist: {str(e)}")


@router.post("/{playlist_id}/add")
async def add_song_to_playlist(
    playlist_id: str,
    request: PlaylistAddSongRequest,
    user: dict = Depends(get_current_user),
):
    """Add a song to a playlist."""
    uid = user["uid"]
    db = get_firestore_client()

    if not db:
        raise HTTPException(status_code=500, detail="Database not available")

    try:
        from google.cloud.firestore_v1 import ArrayUnion

        playlist_ref = db.collection("users").document(uid).collection("playlists").document(playlist_id)

        # Check playlist exists
        doc = playlist_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="Playlist not found")

        # Add song ID to the songs array
        playlist_ref.update({
            "songs": ArrayUnion([{
                "song_id": request.song_id,
                "addedAt": datetime.datetime.now().isoformat(),
            }]),
        })

        return {"success": True, "message": "Song added to playlist"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding song: {str(e)}")
