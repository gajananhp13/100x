import asyncio

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..config import settings
from ..core.ai import get_ai_provider
from ..core.parsers import SUPPORTED_EXTENSIONS, UnsupportedFileError, extract_text
from ..models.report import MessageOut
from ..models.resume import ParsedResume
from ..models.resume import PersonalDetails  # noqa: F401 (schema reference)

router = APIRouter(prefix="/api/resume", tags=["resume"])


@router.post("/upload")
async def upload_resume(file: UploadFile = File(...)) -> dict:
    filename = (file.filename or "").lower()
    if not filename:
        raise HTTPException(status_code=400, detail="No file provided.")
    ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
    if ext not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=415,
            detail=f"Unsupported file type '{ext}'. Upload a PDF or DOCX.",
        )
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB limit.")
    try:
        # PDF/DOCX parsing is CPU-bound and can hang on malformed documents;
        # run it off the event loop so one bad upload cannot block the server.
        text = await asyncio.wait_for(
            run_in_threadpool(extract_text, data, filename),
            timeout=settings.document_parse_timeout_seconds,
        )
    except TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="Document processing timed out. Try a smaller or simpler PDF.",
        ) from None
    except UnsupportedFileError as e:
        raise HTTPException(status_code=415, detail=str(e)) from e
    except Exception:
        raise HTTPException(status_code=422, detail="Could not read text from the document. It may be a scanned image — try a text-based PDF.")
    if len(text.strip()) < 50:
        raise HTTPException(status_code=422, detail="No readable text found in the document.")
    return {
        "message": "Resume uploaded and text extracted.",
        "filename": filename,
        "char_count": len(text),
        "text": text,
        "text_preview": text[:4000],
    }


@router.post("/parse")
async def parse_resume(payload: dict) -> ParsedResume:
    text = (payload.get("text") or "").strip()
    if len(text) < 50:
        raise HTTPException(status_code=422, detail="Resume text is too short to parse.")
    try:
        resume = get_ai_provider(payload.get("ai_mode")).parse_resume(text)
    except Exception as e:  # LLM outage / schema drift -> deterministic fallback
        from ..core.ai import parse_resume_heuristic
        resume = parse_resume_heuristic(text)
    return resume


@router.get("/supported")
async def supported_types() -> dict:
    return {"extensions": sorted(SUPPORTED_EXTENSIONS)}