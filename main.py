"""
Music Hub Backend - FastAPI entry point.
A Firebase-backed music streaming backend with YouTube audio extraction.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging

from config.settings import PORT, HOST, CORS_ORIGINS
from config.firebase_init import initialize_firebase

# Import routers
from routers.auth import router as auth_router
from routers.music import router as music_router
from routers.recommend import router as recommend_router
from routers.smart_recommend import router as smart_recommend_router
from routers.playlist import router as playlist_router
from routers.user import router as user_router
from routers.tracking import router as tracking_router
from routers.auto_playlist import router as auto_playlist_router

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

start_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown."""
    logger.info("Starting Music Hub Backend v2.0.0")
    initialize_firebase()
    logger.info("All systems go!")
    yield
    logger.info("Shutting down Music Hub Backend")


app = FastAPI(
    title="Music Hub Backend",
    description="Firebase-backed music streaming API with YouTube audio extraction",
    version="2.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS if CORS_ORIGINS != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include all routers
app.include_router(auth_router)
app.include_router(music_router)
app.include_router(recommend_router)
app.include_router(smart_recommend_router)
app.include_router(playlist_router)
app.include_router(user_router)
app.include_router(tracking_router)
app.include_router(auto_playlist_router)


@app.get("/", tags=["system"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "service": "Music Hub Backend", "version": "2.0.0"}


@app.get("/health", tags=["system"])
@app.get("/api/health", tags=["system"], include_in_schema=False)
async def health():
    """Detailed health check."""
    uptime = time.time() - start_time
    return {
        "status": "healthy",
        "service": "music-hub-backend",
        "version": "2.0.0",
        "uptime_seconds": round(uptime, 1),
        "endpoints": {
            "auth": "/auth/login",
            "search": "/music/search",
            "play": "/music/play",
            "recommendations": "/recommend/personalized",
            "smart_feed": "/recommend/smart/feed",
            "playlists": "/playlist/my",
            "profile": "/user/profile",
            "tracking": "/track/search",
            "cache_stats": "/api/cache/stats",
        },
    }


@app.get("/api/cache/stats", tags=["cache"])
async def cache_stats():
    """Get cache statistics — hit/miss rates, sizes, TTLs."""
    from services.youtube_service import get_cache_stats
    return get_cache_stats()


@app.delete("/api/cache/clear", tags=["cache"])
async def cache_clear():
    """Clear all in-memory caches and reset counters."""
    from services.youtube_service import clear_caches
    return clear_caches()


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "status_code": 500},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)

