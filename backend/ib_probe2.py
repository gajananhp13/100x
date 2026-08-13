import httpx
import re

r = httpx.get(
    "https://www.interviewbit.com/_next/static/chunks/app/profile/%5Busername%5D/page-3e95447b461119bc.js",
    headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
    timeout=15,
)

# Find the heatmap data fetch function B({username,year})
# Look for the function definition that fetches heatmap data
# Search for patterns like "activity" or "heatmap" near API calls
for kw in ["activity", "heatmap", "submission", "calendar", "study_plan"]:
    for match in re.finditer(kw, r.text, re.IGNORECASE):
        start = max(0, match.start() - 200)
        end = min(len(r.text), match.end() + 300)
        context = r.text[start:end]
        if "api" in context.lower() or "fetch" in context.lower() or "concat" in context.lower():
            print(f"\n=== Context around '{kw}' (pos {match.start()}) ===")
            print(context)
            print()
