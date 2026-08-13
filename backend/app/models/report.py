from datetime import datetime

from pydantic import BaseModel

from .analysis import AnalysisBundle


class CandidateReport(BaseModel):
    report_id: str
    generated_at: datetime
    analysis: AnalysisBundle


class MessageOut(BaseModel):
    message: str