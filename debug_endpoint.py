import httpx
try:
    r = httpx.get("http://127.0.0.1:8000/auto-playlist/test_id", timeout=10)
    with open("debug_out.txt", "w") as f:
        f.write(f"Status: {r.status_code}\n")
        f.write(f"Body: {r.text}\n")
except Exception as e:
    with open("debug_out.txt", "w") as f:
        f.write(f"Error: {e}\n")
