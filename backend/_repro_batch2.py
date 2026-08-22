import sys, asyncio, traceback, json
sys.path.insert(0, r"D:\work Folder\Apps\tests\backend")

from app.core.ai import get_ai_provider
from app.core.integrations import DEMO_RESUME_TEXT
from app.api.routes_integrations import batch_connect

resume = get_ai_provider("mock").parse_resume(DEMO_RESUME_TEXT)
# Inject handles for platforms that have NO registered integration
resume.raw_text += "\nhttps://kaggle.com/johndoe\nhttps://twitter.com/johndoe\nhttps://hashnode.com/@johndoe\nhttps://medium.com/@johndoe"
candidate = {"index": 0, "filename": "demo.txt", "resume": resume.model_dump(mode="json")}

print("detected platforms in resume:")
from app.core.integrations import detect_all
print(list(detect_all(resume).keys()))

try:
    result = asyncio.run(batch_connect({"candidates": [candidate], "simulate": False}))
    print("OK")
    print([p["platform"] for p in result["candidates"][0]["profiles"]])
except Exception:
    traceback.print_exc()
