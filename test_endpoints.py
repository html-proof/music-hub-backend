"""
Music Hub Backend — Endpoint Test Script
Run: python test_endpoints.py
"""

import httpx
import asyncio
import time
import json

BASE_URL = "http://localhost:8000"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


async def test_endpoint(client: httpx.AsyncClient, method: str, path: str, name: str, **kwargs):
    """Test a single endpoint and return result."""
    url = f"{BASE_URL}{path}"
    start = time.perf_counter()

    try:
        if method == "GET":
            resp = await client.get(url, **kwargs)
        else:
            resp = await client.post(url, **kwargs)

        elapsed_ms = (time.perf_counter() - start) * 1000
        status = resp.status_code

        if 200 <= status < 300:
            print(f"  {GREEN}✅ {name:<45}{RESET} {status}  {elapsed_ms:>7.1f}ms")
            return True
        elif status == 401:
            print(f"  {YELLOW}🔑 {name:<45}{RESET} {status}  {elapsed_ms:>7.1f}ms  (needs auth)")
            return True  # Expected for auth-protected endpoints
        else:
            print(f"  {RED}❌ {name:<45}{RESET} {status}  {elapsed_ms:>7.1f}ms")
            return False
    except httpx.ConnectError:
        print(f"  {RED}❌ {name:<45}{RESET} CONNECTION REFUSED")
        return False
    except Exception as e:
        print(f"  {RED}❌ {name:<45}{RESET} ERROR: {e}")
        return False


async def run_tests():
    print(f"\n{BOLD}{CYAN}🎵 Music Hub Backend — Endpoint Tests{RESET}")
    print(f"{CYAN}{'=' * 70}{RESET}\n")

    passed = 0
    failed = 0

    async with httpx.AsyncClient(timeout=30.0) as client:

        # ── Health ──
        print(f"{BOLD}📌 Health Checks{RESET}")
        if await test_endpoint(client, "GET", "/", "Root health check"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/health", "Detailed health"): passed += 1
        else: failed += 1

        # ── Auth ──
        print(f"\n{BOLD}🔐 Auth{RESET}")
        if await test_endpoint(client, "POST", "/auth/login", "Login (no token)", json={"id_token": "test"}): passed += 1
        else: failed += 1

        # ── Music ──
        print(f"\n{BOLD}🎵 Music{RESET}")
        if await test_endpoint(client, "GET", "/music/search?q=shape+of+you", "Search songs"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/music/play?id=dQw4w9WgXcQ&quality=high", "Play (resolve URL)"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "POST", "/music/play", "Play POST", json={"id": "dQw4w9WgXcQ", "quality": "high"}): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/music/play-48k?id=dQw4w9WgXcQ", "Play 48k"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/music/play-64k?id=dQw4w9WgXcQ", "Play 64k"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/music/preview?id=dQw4w9WgXcQ", "Preview"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/music/resolve?id=dQw4w9WgXcQ&quality=high", "Resolve direct URL"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "POST", "/music/prefetch", "Prefetch", json={"ids": ["dQw4w9WgXcQ"], "quality": "high"}): passed += 1
        else: failed += 1

        # ── Recommendations ──
        print(f"\n{BOLD}🎯 Recommendations{RESET}")
        if await test_endpoint(client, "GET", "/recommend/personalized", "Personalized"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/for-you?uid=test", "For You"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/daily-mix?uid=test", "Daily Mix"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/because-liked?uid=test", "Because Liked"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/discover-weekly?uid=test", "Discover Weekly"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/mood?uid=test&mood=chill", "Mood (chill)"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/type?type=pop&language=", "By Type (pop)"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/artist?name=Ed+Sheeran&language=", "By Artist"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/similar?id=dQw4w9WgXcQ", "Similar Songs"): passed += 1
        else: failed += 1

        # ── Smart Recommendations ──
        print(f"\n{BOLD}🧠 Smart Recommendations{RESET}")
        if await test_endpoint(client, "GET", "/recommend/smart/recommendations?limit=5", "Smart Recs"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/smart/feed?page=1&page_size=5", "Smart Feed"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/smart/time-context", "Time Context"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/recommend/smart/quality-stats", "Quality Stats"): passed += 1
        else: failed += 1

        # ── Playlists (auth-protected) ──
        print(f"\n{BOLD}📋 Playlists (auth required){RESET}")
        if await test_endpoint(client, "GET", "/playlist/my", "My Playlists"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "POST", "/playlist/create", "Create Playlist", json={"name": "Test"}): passed += 1
        else: failed += 1

        # ── User (auth-protected) ──
        print(f"\n{BOLD}👤 User (auth required){RESET}")
        if await test_endpoint(client, "GET", "/user/preferences", "Get Preferences"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/user/profile", "Get Profile"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "POST", "/library/like", "Like Song", json={"song_id": "test"}): passed += 1
        else: failed += 1

    # Summary
    total = passed + failed
    print(f"\n{CYAN}{'=' * 70}{RESET}")
    print(f"{BOLD}Results: {GREEN}{passed} passed{RESET} / {RED}{failed} failed{RESET} / {total} total")

    if failed == 0:
        print(f"\n{GREEN}{BOLD}🎉 All endpoints operational!{RESET}\n")
    else:
        print(f"\n{YELLOW}⚠️  Some endpoints need attention.{RESET}\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
