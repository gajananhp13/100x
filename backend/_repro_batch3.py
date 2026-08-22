import sys, json
sys.path.insert(0, r"D:\work Folder\Apps\tests\backend")
from app.core.ai import get_ai_provider
from app.core.integrations import DEMO_RESUME_TEXT
from app.models.resume import ParsedResume

resume = get_ai_provider("mock").parse_resume(DEMO_RESUME_TEXT)
resume.personal.github = "https://github.com/torvalds"
resume.raw_text += "\nhttps://github.com/torvalds"
candidate = {"index": 0, "filename": "real.txt", "resume": resume.model_dump(mode="json")}
with open(r"D:\work Folder\Apps\tests\backend\_payload.json", "w") as f:
    json.dump({"candidates": [candidate], "simulate": False}, f)
print("payload written")
