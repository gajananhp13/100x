"""Analysis route — runs the full pipeline and streams stage progress via SSE,
then stores and returns the Candidate Report."""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse

from ..core.analysis import run_analysis
from ..models.analysis import AnalysisBundle
from ..models.profiles import ConnectedProfile
from ..models.resume import ParsedResume
from ..storage.repo import store

router = APIRouter(prefix="/api/analysis", tags=["analysis"])


@router.post("/run")
async def run(payload: dict) -> StreamingResponse:
    raw_resume = payload.get("resume")
    raw_profiles = payload.get("profiles", [])
    ai_mode = payload.get("ai_mode")

    if not raw_resume:
        raise HTTPException(status_code=422, detail="resume is required.")
    try:
        resume = ParsedResume.model_validate(raw_resume)
        profiles = [ConnectedProfile.model_validate(p) for p in raw_profiles]
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid payload: {e}") from e

    def event(name: str, data: dict) -> str:
        return f"event: {name}\ndata: {json.dumps(data, default=str)}\n\n"

    def generate():
        yield event("stage", {"stage": "init", "message": "Starting candidate verification pipeline…"})

        stages: list[tuple[str, str]] = []

        def cb(stage: str, message: str) -> None:
            stages.append((stage, message))

        try:
            bundle = run_analysis(resume, profiles, on_stage=cb, ai_mode=ai_mode)
        except Exception as e:
            yield event("error", {"message": f"Analysis failed: {e}"})
            return

        for stage, message in stages:
            yield event("stage", {"stage": stage, "message": message})

        report = store.save(bundle)
        yield event("complete", {"report_id": report.report_id, "overall_score": report.analysis.overall_score})

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })


@router.get("/reports")
async def list_reports() -> list[dict]:
    return [
        {
            "report_id": r.report_id,
            "generated_at": r.generated_at.isoformat(),
            "candidate": r.analysis.resume.personal.name,
            "overall_score": r.analysis.overall_score,
        }
        for r in store.list()
    ]


MAX_BATCH_CANDIDATES = 50


@router.post("/batch")
async def run_batch(payload: dict) -> dict:
    """Run the full verification + scoring pipeline across a batch of resumes.

    Each candidate is analysed independently (profiles already connected via the
    HR 'connect all social media' step), stored as its own Candidate Report, and
    the batch is returned ranked by overall score — the HR candidate leaderboard.
    """
    raw_candidates = payload.get("candidates") or []
    ai_mode = payload.get("ai_mode")
    if not raw_candidates:
        raise HTTPException(status_code=422, detail="candidates is required.")
    if len(raw_candidates) > MAX_BATCH_CANDIDATES:
        raise HTTPException(
            status_code=413,
            detail=f"Too many candidates. Analyse at most {MAX_BATCH_CANDIDATES} per batch.",
        )

    async def process(c: dict) -> dict:
        index = c.get("index")
        filename = c.get("filename")
        try:
            resume = ParsedResume.model_validate(c.get("resume"))
            profiles = [ConnectedProfile.model_validate(p) for p in c.get("profiles", [])]
        except Exception as e:  # noqa: BLE001
            return {"index": index, "filename": filename, "error": f"Invalid candidate payload: {e}"}
        try:
            bundle = await run_in_threadpool(run_analysis, resume, profiles, lambda s, m: None, ai_mode)
        except Exception as e:  # noqa: BLE001 - one candidate must not sink the batch
            return {"index": index, "filename": filename, "error": f"Analysis failed: {e}"}
        report = store.save(bundle)
        return {
            "index": index,
            "filename": filename,
            "report_id": report.report_id,
            "candidate_name": resume.personal.name or "Candidate",
            "overall_score": report.analysis.overall_score,
            "scores": [s.model_dump(mode="json") for s in report.analysis.scores],
        }

    results = await asyncio.gather(*[process(c) for c in raw_candidates])
    candidates = [r for r in results if "error" not in r]
    errors = [r for r in results if "error" in r]

    candidates.sort(key=lambda r: float(r.get("overall_score") or 0), reverse=True)
    for rank, c in enumerate(candidates, 1):
        c["rank"] = rank

    return {
        "processed": len(candidates),
        "failed": len(errors),
        "candidates": candidates,
        "errors": errors,
    }