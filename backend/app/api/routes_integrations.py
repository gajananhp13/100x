from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from ..core.ai import get_ai_provider
from ..core.ai.genkit_flow import scrape_github_profile
from ..core.integrations import (
    DEMO_NAME,
    DEMO_PROFILES,
    DEMO_RESUME_TEXT,
    PLATFORM_BY_ID,
    ProfileCollectError,
    build_integration,
    detect_all,
    detect_handle,
    platform_categories,
    url_for,
)
from ..models.profiles import ConnectRequest, ConnectResponse, ConnectedProfile
from ..models.resume import ParsedResume

router = APIRouter(prefix="/api/integrations", tags=["integrations"])


@router.get("/platforms")
async def platforms() -> dict:
    return {"categories": platform_categories(), "platforms": list(PLATFORM_BY_ID.values())}


@router.post("/connect", response_model=ConnectResponse)
async def connect_profile(req: ConnectRequest) -> ConnectResponse:
    handle = (req.handle or "").strip().lstrip("@").rstrip("/")
    if not handle and req.resume:
        # Auto-detect: the handle can be read straight from the resume
        detected = detect_handle(req.platform, req.resume)
        if detected:
            handle = detected
    if not handle:
        raise HTTPException(status_code=422, detail="Handle cannot be empty.")
    if req.platform not in PLATFORM_BY_ID:
        raise HTTPException(status_code=404, detail=f"Unknown platform '{req.platform}'.")
    integration = build_integration(req.platform, force_mock=req.simulate)
    try:
        data = integration.collect(handle, {"resume": req.resume})
    except ProfileCollectError as e:
        return ConnectResponse(profile=None, message=str(e))
    except Exception as e:
        return ConnectResponse(profile=None, message=f"Could not connect: {e}")

    clean_handle = str(data.get("username") or handle).lstrip("@")
    profile = ConnectedProfile(
        platform=req.platform,
        platform_label=PLATFORM_BY_ID[req.platform].label,
        handle=clean_handle,
        profile_url=url_for(req.platform, clean_handle),
        status="collected",
        collected_at=datetime.now(timezone.utc),
        data=data,
    )
    return ConnectResponse(profile=profile, message="Profile connected.")


@router.post("/detect")
async def detect_profiles(payload: dict) -> dict:
    """Auto-detect which platform handles exist in the resume — no user input needed.

    Scans the parsed personal fields (github, linkedin, portfolio) and the raw
    resume body for profile URLs, returning a platform-id -> handle map.
    """
    raw_resume = payload.get("resume")
    if not raw_resume:
        raise HTTPException(status_code=422, detail="resume is required.")
    try:
        resume = ParsedResume.model_validate(raw_resume)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid resume payload: {e}") from e
    return {"handles": detect_all(resume)}


@router.post("/auto-connect")
async def auto_connect(payload: dict) -> dict:
    """Detect every platform mentioned in the resume and connect them all.

    For platforms whose handle appears in the resume (GitHub, LinkedIn, LeetCode,
    ...), this collects the profile data directly — the user never types a handle.
    """
    raw_resume = payload.get("resume")
    simulate = bool(payload.get("simulate", False))
    if not raw_resume:
        raise HTTPException(status_code=422, detail="resume is required.")
    try:
        resume = ParsedResume.model_validate(raw_resume)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Invalid resume payload: {e}") from e

    handles = detect_all(resume)
    profiles: list[dict] = []
    skipped: list[str] = []
    for platform_id, handle in handles.items():
        try:
            integration = build_integration(platform_id, force_mock=simulate)
            data = integration.collect(handle, {"resume": resume})
        except Exception as e:  # noqa: BLE001 - one failed platform must not block the rest
            skipped.append(f"{platform_id} ({e})")
            continue
        clean_handle = str(data.get("username") or handle).lstrip("@")
        profiles.append(
            ConnectedProfile(
                platform=platform_id,
                platform_label=PLATFORM_BY_ID[platform_id].label,
                handle=clean_handle,
                profile_url=url_for(platform_id, clean_handle),
                status="collected",
                collected_at=datetime.now(timezone.utc),
                data=data,
            ).model_dump(mode="json")
        )

    return {
        "message": f"Auto-connected {len(profiles)} profile(s) detected in the resume.",
        "handles": handles,
        "profiles": profiles,
        "skipped": skipped,
    }


@router.post("/github/genkit")
async def github_profile_via_genkit(req: ConnectRequest) -> dict:
    """Scrape a GitHub profile through the Genkit flow (scrapeGithubProfile)."""
    handle = (req.handle or "").strip().lstrip("@").rstrip("/")
    if not handle and req.resume:
        detected = detect_handle("github", req.resume)
        if detected:
            handle = detected
    if not handle:
        raise HTTPException(status_code=422, detail="Handle cannot be empty.")
    result = await scrape_github_profile(handle)
    return {
        "flow": scrape_github_profile.name,
        "success": result.success,
        "data": result.data,
        "summary": result.summary,
        "error": result.error,
        "cached": result.cached,
    }


@router.post("/demo")
async def demo_candidate(simulate: bool = True) -> dict:
    """Load the demo candidate: parsed resume + all platforms pre-connected."""
    resume = get_ai_provider("mock").parse_resume(DEMO_RESUME_TEXT)
    profiles: list[ConnectedProfile] = []
    for pid, handle in DEMO_PROFILES.items():
        try:
            data = build_integration(pid, force_mock=simulate).collect(handle, {"resume": resume})
            profiles.append(
                ConnectedProfile(
                    platform=pid,
                    platform_label=PLATFORM_BY_ID[pid].label,
                    handle=handle,
                    profile_url=url_for(pid, handle),
                    status="collected",
                    collected_at=datetime.now(timezone.utc),
                    data=data,
                )
            )
        except ProfileCollectError:
            continue
    return {
        "message": f"Demo candidate '{DEMO_NAME}' loaded.",
        "candidate_name": DEMO_NAME,
        "resume": resume,
        "profiles": profiles,
        "simulated": True,
    }