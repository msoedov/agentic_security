from pathlib import Path
from fastapi import APIRouter
from fastapi.responses import FileResponse
from ..models.schemas import Settings

router = APIRouter()


@router.get("/")
async def root():
    agentic_security_path = Path(__file__).parent.parent
    return FileResponse(f"{agentic_security_path}/static/index.html")


@router.get("/main.js")
async def main_js():
    agentic_security_path = Path(__file__).parent.parent
    return FileResponse(f"{agentic_security_path}/static/main.js")


@router.get("/telemetry.js")
async def telemetry_js():
    agentic_security_path = Path(__file__).parent.parent
    if Settings.DISABLE_TELEMETRY:
        return FileResponse(f"{agentic_security_path}/static/telemetry_disabled.js")
    return FileResponse(f"{agentic_security_path}/static/telemetry.js")


@router.get("/favicon.ico")
async def favicon():
    agentic_security_path = Path(__file__).parent.parent
    return FileResponse(f"{agentic_security_path}/static/favicon.ico")
