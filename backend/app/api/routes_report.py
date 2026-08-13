from fastapi import APIRouter, HTTPException

from ..models.report import CandidateReport
from ..storage.repo import store

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/{report_id}", response_model=CandidateReport)
async def get_report(report_id: str) -> CandidateReport:
    report = store.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    return report


@router.get("/{report_id}/pdf")
async def download_pdf(report_id: str):
    report = store.get(report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found.")
    from ..core.report.pdf import render_pdf

    pdf_bytes = render_pdf(report)
    candidate = report.analysis.resume.personal.name or "candidate"
    import re

    filename = f"100x-resume-{re.sub(r'[^a-z0-9]+', '-', candidate.lower())}-{report_id}.pdf"
    from fastapi.responses import Response

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )