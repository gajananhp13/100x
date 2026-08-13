from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import routes_analysis, routes_integrations, routes_report, routes_resume
from .config import settings
from .core.ai import check_openai_available

app = FastAPI(title=settings.app_name, version="1.0.0", description="AI Candidate Verification & Resume Intelligence Platform")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_resume.router)
app.include_router(routes_integrations.router)
app.include_router(routes_analysis.router)
app.include_router(routes_report.router)


@app.get("/api/health")
async def health() -> dict:
    return {
        "status": "ok",
        "app": settings.app_name,
        "ai_provider": "openai" if settings.openai_api_key else "mock",
        "openai_reachable": await check_openai_available() if settings.openai_api_key else False,
    }