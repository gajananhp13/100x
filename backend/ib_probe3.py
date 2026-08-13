import httpx
import json

with httpx.Client(
    headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml",
    },
    follow_redirects=True,
    timeout=20,
) as client:
    # Step 1: hit the profile page to get session cookies
    profile_resp = client.get("https://www.interviewbit.com/profile/Gajananhp/")
    print("Profile page status:", profile_resp.status_code)
    print("Cookies:", dict(client.cookies))

    # Step 2: hit the API endpoints with cookies
    for path in [
        "username/daily-user-submissions/2026/?id=Gajananhp",
        "username/submission-analysis/?id=Gajananhp",
    ]:
        r = client.get(
            f"https://www.interviewbit.com/{path}",
            headers={"Accept": "application/json", "Referer": "https://www.interviewbit.com/profile/Gajananhp/"},
        )
        ct = r.headers.get("content-type", "?")[:30]
        print(f"\n{path}: {r.status_code} ({ct})")
        if r.status_code == 200:
            try:
                d = r.json()
                print(json.dumps(d, indent=2)[:1500])
            except Exception:
                print(r.text[:500])
        else:
            print(r.text[:300])
