"""Report storage — JSON files under the configured directory.

Kept behind a tiny interface so a real database can be swapped in later.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from ..config import settings
from ..models.report import CandidateReport


class ReportStore:
    def __init__(self, directory: str | None = None) -> None:
        self.directory = Path(directory or settings.report_storage_dir)
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, report_id: str) -> Path:
        return self.directory / f"{report_id}.json"

    def save(self, analysis) -> CandidateReport:
        report_id = uuid.uuid4().hex[:12]
        report = CandidateReport(report_id=report_id, generated_at=datetime.now(), analysis=analysis)
        self._path(report_id).write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return report

    def get(self, report_id: str) -> CandidateReport | None:
        path = self._path(report_id)
        if not path.exists():
            return None
        try:
            return CandidateReport.model_validate_json(path.read_text(encoding="utf-8"))
        except Exception:
            return None

    def list(self) -> list[CandidateReport]:
        out = []
        for path in sorted(self.directory.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[:50]:
            try:
                out.append(CandidateReport.model_validate_json(path.read_text(encoding="utf-8")))
            except Exception:
                continue
        return out


store = ReportStore()
