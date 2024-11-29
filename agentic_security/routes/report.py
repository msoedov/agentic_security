from pathlib import Path

from fastapi import APIRouter, Response
from fastapi.responses import FileResponse, StreamingResponse

from ..models.schemas import Table
from ..report_chart import plot_security_report

router = APIRouter()


@router.get("/failures")
async def failures_csv():
    if not Path("failures.csv").exists():
        return {"error": "No failures found"}
    return FileResponse("failures.csv")


@router.post("/plot.jpeg", response_class=Response)
async def get_plot(table: Table):
    buf = plot_security_report(table.table)
    return StreamingResponse(buf, media_type="image/jpeg")
