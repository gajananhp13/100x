"""Analysis route — runs the full pipeline and streams stage progress via SSE,
then stores and returns the Candidate Report."""

from __future__ import annotations

import json

from fastapi import APIRouter, HTTPException
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