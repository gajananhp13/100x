import sys, traceback, asyncio
sys.path.insert(0, r"D:\work Folder\Apps\tests\backend")

from app.core.ai import get_ai_provider
from app.core.integrations import DEMO_RESUME_TEXT
from app.api.routes_integrations import batch_connect

resume = get_ai_provider("mock").parse_resume(DEMO_RESUME_TEXT)
candidate = {"index": 0, "filename": "demo.txt", "resume": resume.model_dump(mode="json")}

try:
    result = asyncio.run(batch_connect({"candidates": [candidate], "simulate": False}))
    print("OK", result)
except Exception:
    traceback.print_exc()
