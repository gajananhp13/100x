import httpx
import re
import json

resp = httpx.get(
    "https://www.interviewbit.com/profile/Gajananhp",
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    },
    timeout=20,
    follow_redirects=True,
)

# Extract all RSC chunks
chunks = re.findall(r'self\.__next_f\.push\(\[1,"(.*?)"\]\)', resp.text)
print(f"Found {len(chunks)} RSC chunks")

# Look for profile data in chunks
for i, chunk in enumerate(chunks):
    try:
        decoded = chunk.encode("utf-8").decode("unicode_escape")
    except Exception:
        decoded = chunk
    # Print chunks that might contain profile data
    lower = decoded.lower()
    if any(kw in lower for kw in ["streak", "problems_solved", "solved", "score", "level", "badge", "username", "profile"]):
        print(f"\n--- Chunk {i} (profile-related) ---")
        print(decoded[:500])
