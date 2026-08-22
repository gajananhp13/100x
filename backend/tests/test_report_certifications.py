"""Tests that LinkedIn certifications appear in the generated PDF report."""

from __future__ import annotations

from datetime import datetime, timezone

from app.core.report.pdf import render_pdf
from app.models.analysis import AnalysisBundle
from app.models.profiles import ConnectedProfile
from app.models.report import CandidateReport
from app.models.resume import ParsedResume


def _bundle_with_linkedin(certs: list[dict] | None) -> AnalysisBundle:
    resume = ParsedResume(personal={"name": "Aarav Mehta"})
    profiles = []
    if certs is not None:
        profiles.append(
            ConnectedProfile(
                platform="linkedin",
                platform_label="LinkedIn",
                handle="aaravmehta",
                status="collected",
                data={"certifications": certs},
            )
        )
    return AnalysisBundle(resume=resume, profiles=profiles)


def _pdf_text(certs: list[dict] | None) -> str:
    bundle = _bundle_with_linkedin(certs)
    report = CandidateReport(
        report_id="test",
        generated_at=datetime.now(timezone.utc),
        analysis=bundle,
    )
    pdf_bytes = render_pdf(report)
    import fitz

    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    return "".join(page.get_text() for page in doc)


def test_pdf_includes_linkedin_certifications():
    text = _pdf_text(
        [
            {
                "title": "AWS Certified Cloud Practitioner",
                "issuer": "Amazon Web Services",
                "issued_date": "2024",
                "credential_id": "ABC-123",
                "credential_url": "https://credly.com/x",
            }
        ]
    )
    assert "LinkedIn Certifications" in text
    assert "AWS Certified Cloud Practitioner" in text
    assert "Amazon Web Services" in text


def test_pdf_handles_linkedin_without_certifications():
    text = _pdf_text([])
    assert "LinkedIn Certifications" in text
    assert "No certifications listed" in text


def test_pdf_handles_no_linkedin_profile():
    text = _pdf_text(None)
    # Report renders without the LinkedIn certifications section entirely
    assert "LinkedIn Certifications" not in text
