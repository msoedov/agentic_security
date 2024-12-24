from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import StreamingResponse

from ..core.app import get_stop_event, get_tools_inbox, set_current_run
from ..http_spec import LLMSpec
from ..models.schemas import LLMInfo, Scan
from ..probe_actor import fuzzer

router = APIRouter()


@router.post("/verify")
async def verify(info: LLMInfo):
    spec = LLMSpec.from_string(info.spec)
    r = await spec.verify()
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return dict(
        status_code=r.status_code,
        body=r.text,
        elapsed=r.elapsed.total_seconds(),
        timestamp=datetime.now().isoformat(),
    )


def streaming_response_generator(scan_parameters: Scan):
    request_factory = LLMSpec.from_string(scan_parameters.llmSpec)
    set_current_run(request_factory)

    async def _gen():
        async for scan_result in fuzzer.scan_router(
            request_factory=request_factory,
            scan_parameters=scan_parameters,
            tools_inbox=get_tools_inbox(),
            stop_event=get_stop_event(),
        ):
            yield scan_result + "\n"

    return _gen()


@router.post("/scan")
async def scan(scan_parameters: Scan, background_tasks: BackgroundTasks):
    return StreamingResponse(
        streaming_response_generator(scan_parameters), media_type="application/json"
    )


@router.post("/stop")
async def stop_scan():
    get_stop_event().set()
    return {"status": "Scan stopped"}
