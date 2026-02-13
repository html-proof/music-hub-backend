"""
Test all endpoints — system, auth, tracking, recommendations, user.
Auth-required endpoints should return 401 (HTTPBearer spec) when no token provided.
"""

import httpx
import time
import json
import sys

BASE = "http://127.0.0.1:8000"

passed = 0
failed = 0
results = []


def test(method, path, name, expect_code=200, body=None, headers=None):
    global passed, failed
    url = f"{BASE}{path}"
    start = time.perf_counter()
    try:
        if method == "GET":
            r = httpx.get(url, headers=headers, timeout=30)
        elif method == "DELETE":
            r = httpx.delete(url, headers=headers, timeout=30)
        else:
            r = httpx.post(url, json=body, headers=headers, timeout=30)
        ms = (time.perf_counter() - start) * 1000

        ok = r.status_code == expect_code
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        results.append((name, method, path, r.status_code, expect_code, ms, status))
    except Exception as e:
        ms = (time.perf_counter() - start) * 1000
        failed += 1
        results.append((name, method, path, "ERR", expect_code, ms, f"FAIL: {e}"))
    
    if not ok:
        print(f"❌ {name} FAILED: Got {r.status_code}, expected {expect_code}")
        print(f"Response: {r.text[:200]}")


# ==================== SYSTEM ENDPOINTS ====================
test("GET", "/", "Root health")
test("GET", "/health", "Detailed health")
test("GET", "/api/health", "/api/health alias")

# ==================== CACHE ENDPOINTS ====================
test("GET", "/api/cache/stats", "Cache stats")
test("DELETE", "/api/cache/clear", "Cache clear")

# ==================== AUTH ENDPOINTS ====================
test("POST", "/auth/login", "Auth login (empty token)", expect_code=422,
     body={"firebase_token": ""})
test("POST", "/auth/logout", "Auth logout (no auth)", expect_code=401)
test("GET", "/auth/me", "Auth me (no auth)", expect_code=401)

# ==================== MUSIC ENDPOINTS ====================
test("GET", "/music/search?q=shape+of+you", "Music search")
test("GET", "/music/search?q=shape+of+you", "Music search (cached)")

# ==================== RECOMMENDATION ENDPOINTS ====================
test("GET", "/recommend/personalized", "Personalized recs")
test("GET", "/recommend/for-you?uid=test", "For you recs")
test("GET", "/recommend/mood?mood=chill&uid=test", "Mood recs")

# ==================== SMART RECOMMENDATION ENDPOINTS ====================
test("GET", "/recommend/smart/time-context", "Smart time context")
test("GET", "/recommend/smart/quality-stats", "Smart quality stats")

# ==================== TRACKING ENDPOINTS (401 = no bearer) ====================
test("POST", "/track/search", "Track search (no auth)", expect_code=401,
     body={"search_query": "test"})
test("POST", "/track/play", "Track play (no auth)", expect_code=401,
     body={"video_id": "abc", "title": "Test"})
test("POST", "/track/skip", "Track skip (no auth)", expect_code=401,
     body={"play_id": "abc"})
test("POST", "/track/complete", "Track complete (no auth)", expect_code=401,
     body={"play_id": "abc"})
test("POST", "/track/click", "Track click (no auth)", expect_code=401,
     body={"search_id": "abc", "video_id": "xyz"})
test("GET", "/track/search-history", "Search history (no auth)", expect_code=401)
test("GET", "/track/play-history", "Play history (no auth)", expect_code=401)
test("GET", "/track/activity-log", "Activity log (no auth)", expect_code=401)
test("GET", "/track/keywords", "User keywords (no auth)", expect_code=401)
test("GET", "/track/suggestions?q=test", "Suggestions (no auth)", expect_code=401)

# ==================== USER ENDPOINTS (401 = no bearer) ====================
test("GET", "/user/check-onboarding", "Check onboarding (no auth)", expect_code=401)
test("POST", "/user/onboarding", "Save onboarding (no auth)", expect_code=401,
     body={"language": "hindi", "moods": ["romantic"]})
test("GET", "/user/preferences", "Get preferences (no auth)", expect_code=401)
test("GET", "/user/profile", "Get profile (no auth)", expect_code=401)
test("GET", "/user/insights", "Get insights (no auth)", expect_code=401)
test("GET", "/user/home-feed", "Get home feed (no auth)", expect_code=401)
test("POST", "/library/like", "Like song (no auth)", expect_code=401,
     body={"song_id": "test"})

# ==================== PLAYLIST ENDPOINTS ====================
test("GET", "/playlist/my", "My playlists (optional auth)", expect_code=200)
test("POST", "/playlist/create", "Create playlist (no auth)", expect_code=401,
     body={"name": "test"})

# ==================== AUTO-PLAYLIST ENDPOINTS (401 = no bearer) ====================
test("POST", "/auto-playlist/generate?algorithm=smart", "Auto-playlist gen (no auth)", expect_code=401)
test("GET", "/auto-playlist/list", "Auto-playlist list (no auth)", expect_code=401)
test("GET", "/auto-playlist/test_id", "Get auto-playlist", expect_code=404)
test("DELETE", "/auto-playlist/history/clear", "Clear history (no auth)", expect_code=401)

# ==================== PRINT RESULTS ====================
print()
print("=" * 75)
print(f"  MUSIC HUB BACKEND — ENDPOINT TEST RESULTS")
print("=" * 75)
print(f"  {'Test':<35} {'Method':<6} {'Got':>4} {'Exp':>4} {'Time':>8}  Result")
print("-" * 75)

for name, method, path, got, exp, ms, status in results:
    icon = "OK" if "PASS" in status else "XX"
    print(f"  {name:<35} {method:<6} {str(got):>4} {str(exp):>4} {ms:>7.1f}ms  {icon}")

print("-" * 75)
print(f"  PASSED: {passed}  |  FAILED: {failed}  |  TOTAL: {passed + failed}")
print("=" * 75)

sys.exit(0 if failed == 0 else 1)
