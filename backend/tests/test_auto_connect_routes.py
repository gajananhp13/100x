from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest

from app.core.integrations.demo import DEMO_RESUME_TEXT
from app.main import app

pytestmark = pytest.mark.asyncio


@asynccontextmanager
async def _client() -> AsyncIterator[httpx.AsyncClient]:
    async with httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c


async def _parsed_demo_resume(client: httpx.AsyncClient) -> dict:
    res = await client.post("/api/resume/parse", json={"text": DEMO_RESUME_TEXT})
    assert res.status_code == 200
    return res.json()


async def test_detect_returns_handles_from_resume():
    async with _client() as client:
        resume = await _parsed_demo_resume(client)
        det = await client.post("/api/integrations/detect", json={"resume": resume})
        assert det.status_code == 200
        handles = det.json()["handles"]
        assert handles["github"] == "aarav-mehta"
        assert handles["linkedin"] == "aaravmehta"


async def test_auto_connect_connects_detected_profiles():
    async with _client() as client:
        resume = await _parsed_demo_resume(client)
        ac = await client.post("/api/integrations/auto-connect", json={"resume": resume, "simulate": True})
        assert ac.status_code == 200
        body = ac.json()
        assert body["message"].startswith("Auto-connected")
        assert {p["platform"] for p in body["profiles"]} == {"github", "linkedin"}
        assert body["profiles"][0]["handle"] == "aarav-mehta"


async def test_connect_without_handle_detects_from_resume():
    async with _client() as client:
        resume = await _parsed_demo_resume(client)
        cn = await client.post(
            "/api/integrations/connect",
            json={"platform": "github", "handle": "", "resume": resume, "simulate": True},
        )
        assert cn.status_code == 200
        assert cn.json()["profile"]["handle"] == "aarav-mehta"


async def test_connect_without_handle_and_no_resume_link_fails():
    async with _client() as client:
        cn = await client.post(
            "/api/integrations/connect",
            json={"platform": "github", "handle": "", "resume": None},
        )
        assert cn.status_code == 422
        assert "empty" in cn.json()["detail"]


async def test_detect_requires_resume():
    async with _client() as client:
        det = await client.post("/api/integrations/detect", json={})
        assert det.status_code == 422