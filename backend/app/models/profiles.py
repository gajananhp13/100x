from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

PlatformStatus = Literal["collected", "failed", "pending"]


class ConnectedProfile(BaseModel):
    platform: str
    platform_label: str
    handle: str
    profile_url: str | None = None
    status: PlatformStatus = "pending"
    collected_at: datetime | None = None
    error: str | None = None
    data: dict[str, Any] = Field(default_factory=dict)


class ConnectRequest(BaseModel):
    platform: str
    handle: str | None = None  # optional: auto-detected from resume when empty
    simulate: bool = False
    resume: "ParsedResume | None" = None


from .resume import ParsedResume  # noqa: E402  (forward reference for connect context)


class ConnectResponse(BaseModel):
    profile: ConnectedProfile | None = None
    message: str
