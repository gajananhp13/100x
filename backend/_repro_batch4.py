import sys, asyncio, traceback
sys.path.insert(0, r"D:\work Folder\Apps\tests\backend")
from app.core.ai import get_ai_provider
from app.core.integrations import DEMO_RESUME_TEXT
from app.api.routes_integrations import batch_connect

resume = get_ai_provider("mock").parse_resume(DEMO_RESUME_TEXT)
handles = [
    "https://github.com/aarav-mehta",
    "https://leetcode.com/u/aarav",
    "https://codeforces.com/profile/aarav",
    "https://codechef.com/users/aarav",
    "https://auth.geeksforgeeks.org/user/aarav",
    "https://hackerrank.com/aarav",
    "https://gitlab.com/aarav",
    "https://bitbucket.org/aarav",
    "https://devpost.com/aarav",
    "https://stackoverflow.com/users/123/aarav",
    "https://linkedin.com/in/aarav",
    "https://aarav.dev",
    "https://medium.com/@aarav",
    "https://hashnode.com/@aarav",
    "https://dev.to/aarav",
    "https://twitter.com/aarav",
    "https://kaggle.com/aarav",
    "https://interviewbit.com/profile/aarav",
]
resume.raw_text = DEMO_RESUME_TEXT + "\n" + "\n".join(handles)
resume.personal.github = "https://github.com/aarav-mehta"
resume.personal.linkedin = "https://linkedin.com/in/aarav"
resume.personal.portfolio = "https://aarav.dev"
candidate = {"index": 0, "filename": "multi.txt", "resume": resume.model_dump(mode="json")}

try:
    res = asyncio.run(batch_connect({"candidates": [candidate], "simulate": False}))
    print("OK platforms:", [p["platform"] for p in res["candidates"][0]["profiles"]])
except Exception:
    print("=== EXCEPTION (this is the 500 source) ===")
    traceback.print_exc()
