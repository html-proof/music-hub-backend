"""
Music Hub Backend — Live API Test Script
Target: https://web-production-11764.up.railway.app/
"""

import httpx
import asyncio
import time
import json
import os

# Live URL
BASE_URL = "https://web-production-11764.up.railway.app"

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
        # Add a timeout for the request
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
        elif status == 404:
             print(f"  {RED}❌ {name:<45}{RESET} {status}  {elapsed_ms:>7.1f}ms (Not Found)")
             return False
        else:
            print(f"  {RED}❌ {name:<45}{RESET} {status}  {elapsed_ms:>7.1f}ms")
            # Print error detail if available
            try:
                print(f"     {YELLOW}Response: {resp.text[:100]}{RESET}")
            except:
                pass
            return False
    except httpx.ConnectError:
        print(f"  {RED}❌ {name:<45}{RESET} CONNECTION REFUSED")
        return False
    except httpx.TimeoutException:
        print(f"  {RED}❌ {name:<45}{RESET} TIMEOUT")
        return False
    except Exception as e:
        print(f"  {RED}❌ {name:<45}{RESET} ERROR: {e}")
        return False


async def run_tests():
    print(f"\n{BOLD}{CYAN}🎵 Music Hub Backend — Live API Tests{RESET}")
    print(f"Target: {BASE_URL}")
    print(f"{CYAN}{'=' * 70}{RESET}\n")

    passed = 0
    failed = 0
    
    # Increase timeout for live server latency
    timeout = httpx.Timeout(45.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:

        # ── Health ──
        print(f"{BOLD}📌 Health Checks{RESET}")
        if await test_endpoint(client, "GET", "/", "Root health check"): passed += 1
        else: failed += 1
        if await test_endpoint(client, "GET", "/health", "Detailed health"): passed += 1
        else: failed += 1

        # ── Auth ──
        print(f"\n{BOLD}🔐 Auth{RESET}")
        # Note: This will likely fail or return 400/401 without a real token, but we check connectivity
        if await test_endpoint(client, "POST", "/auth/login", "Login (dummy token)", json={"id_token": "test_token_dummy"}): passed += 1
        else: failed += 1

        # ── Music ──
        print(f"\n{BOLD}🎵 Music{RESET}")
        if await test_endpoint(client, "GET", "/music/search?q=shape+of+you", "Search songs"): passed += 1
        else: failed += 1
        
        # Use a known ID if possible, or one from search if we were dynamic, but we'll use the rickroll ID as a static test
        test_id = "dQw4w9WgXcQ"
        
        if await test_endpoint(client, "GET", f"/music/play?id={test_id}&quality=high", "Play (resolve URL)"): passed += 1
        else: failed += 1
        
        if await test_endpoint(client, "POST", "/music/play", "Play POST", json={"id": test_id, "quality": "high"}): passed += 1
        else: failed += 1
        
        if await test_endpoint(client, "GET", f"/music/preview?id={test_id}", "Preview"): passed += 1
        else: failed += 1

        # ── Recommendations ──
        print(f"\n{BOLD}🎯 Recommendations{RESET}")
        # These might fail if the backend relies on firebase auth heavily for these, but let's see
        if await test_endpoint(client, "GET", "/recommend/personalized", "Personalized"): passed += 1
        else: failed += 1
        
        if await test_endpoint(client, "GET", "/recommend/smart/recommendations?limit=5", "Smart Recs"): passed += 1
        else: failed += 1

    # Summary
    total = passed + failed
    print(f"\n{CYAN}{'=' * 70}{RESET}")
    print(f"{BOLD}Results: {GREEN}{passed} passed{RESET} / {RED}{failed} failed{RESET} / {total} total")

    if failed == 0:
        print(f"\n{GREEN}{BOLD}🎉 All tests passed!{RESET}\n")
    else:
        print(f"\n{YELLOW}⚠️  Some tests failed.{RESET}\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
