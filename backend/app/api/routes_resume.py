import asyncio
import logging

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from ..config import settings
from ..core.ai import get_ai_provider
from ..core.parsers import SUPPORTED_EXTENSIONS, UnsupportedFileError, extract_text
from ..models.report import MessageOut
from ..models.resume import ParsedResume
from ..models.resume import PersonalDetails  # noqa: F401 (schema reference)

logger = logging.getLogger(__name__)

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


def _parse_text(text: str, ai_mode: str | None = None) -> ParsedResume:
    """Parse resume text into a structured model with a deterministic fallback."""
    try:
        return get_ai_provider(ai_mode).parse_resume(text)
    except Exception:
        from ..core.ai import parse_resume_heuristic

        return parse_resume_heuristic(text)


@router.post("/parse")
async def parse_resume(payload: dict) -> ParsedResume:
    text = (payload.get("text") or "").strip()
    if len(text) < 50:
        raise HTTPException(status_code=422, detail="Resume text is too short to parse.")
    try:
        resume = _parse_text(text, payload.get("ai_mode"))
    except Exception as e:  # heuristic parser must never leak a 500
        logger.exception("Resume parsing failed: %s", e)
        raise HTTPException(
            status_code=422,
            detail="Could not parse this resume. Please check the formatting and try again.",
        ) from None
    return resume


MAX_BATCH_FILES = 50


@router.post("/batch")
async def upload_resume_batch(files: list[UploadFile] = File(...)) -> dict:
    """Upload and parse many resumes at once for the HR ranking flow.

    Each file is extracted, parsed and returned as a structured candidate so the
    client can connect profiles and run validation across the whole batch. A
    single bad file never blocks the rest of the batch.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    if len(files) > MAX_BATCH_FILES:
        raise HTTPException(
            status_code=413,
            detail=f"Too many files. Upload at most {MAX_BATCH_FILES} resumes per batch.",
        )

    candidates: list[dict] = []
    errors: list[dict] = []

    for idx, file in enumerate(files):
        filename = (file.filename or "").lower()
        display_name = file.filename or f"file_{idx}"
        if not filename:
            errors.append({"filename": display_name, "detail": "Empty filename."})
            continue
        ext = "." + filename.rsplit(".", 1)[-1] if "." in filename else ""
        if ext not in SUPPORTED_EXTENSIONS:
            errors.append({"filename": display_name, "detail": f"Unsupported file type '{ext}'."})
            continue
        try:
            data = await file.read()
        except Exception:
            errors.append({"filename": display_name, "detail": "Could not read the uploaded file."})
            continue
        if len(data) > settings.max_upload_bytes:
            errors.append({"filename": display_name, "detail": "File exceeds the 10 MB limit."})
            continue
        try:
            text = await asyncio.wait_for(
                run_in_threadpool(extract_text, data, filename),
                timeout=settings.document_parse_timeout_seconds,
            )
        except TimeoutError:
            errors.append({"filename": display_name, "detail": "Document processing timed out."})
            continue
        except UnsupportedFileError as e:
            errors.append({"filename": display_name, "detail": str(e)})
            continue
        except Exception:
            errors.append(
                {"filename": display_name, "detail": "Could not read text from the document."}
            )
            continue
        if len(text.strip()) < 50:
            errors.append({"filename": display_name, "detail": "No readable text found in the document."})
            continue
        try:
            resume = _parse_text(text)
        except Exception as e:
            errors.append({"filename": display_name, "detail": f"Could not parse this resume: {e}"})
            continue
        candidates.append(
            {
                "index": idx,
                "filename": display_name,
                "resume": resume.model_dump(mode="json"),
                "text_preview": text[:4000],
            }
        )

    return {
        "processed": len(candidates),
        "failed": len(errors),
        "candidates": candidates,
        "errors": errors,
    }


@router.get("/supported")
async def supported_types() -> dict:
    return {"extensions": sorted(SUPPORTED_EXTENSIONS)}