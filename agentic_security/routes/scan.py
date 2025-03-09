from collections.abc import Generator
from datetime import datetime
from typing import Any

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
)
from fastapi.responses import StreamingResponse

from agentic_security.logutils import logger

from ..core.app import get_stop_event, get_tools_inbox, set_current_run
from ..dependencies import InMemorySecrets, get_in_memory_secrets
from ..http_spec import LLMSpec
from ..primitives import LLMInfo, Scan
from ..probe_actor import fuzzer

router = APIRouter()


@router.post("/verify")
async def verify(
    info: LLMInfo, secrets: InMemorySecrets = Depends(get_in_memory_secrets)
) -> dict[str, int | str | float]:
    spec = LLMSpec.from_string(info.spec)
    try:
        r = await spec.verify()
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=400, detail=str(e))

    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return dict(
        status_code=r.status_code,
        body=r.text,
        elapsed=r.elapsed.total_seconds(),
        timestamp=datetime.now().isoformat(),
    )


def streaming_response_generator(scan_parameters: Scan) -> Generator[str, Any, None]:
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
async def scan(
    scan_parameters: Scan,
    background_tasks: BackgroundTasks,
    secrets: InMemorySecrets = Depends(get_in_memory_secrets),
) -> StreamingResponse:
    scan_parameters.with_secrets(secrets)
    return StreamingResponse(
        streaming_response_generator(scan_parameters), media_type="application/json"
    )


@router.post("/stop")
async def stop_scan() -> dict[str, str]:
    get_stop_event().set()
    return {"status": "Scan stopped"}


@router.post("/scan-csv")
async def scan_csv(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    llmSpec: UploadFile = File(...),
    optimize: bool = Query(False),
    maxBudget: int = Query(10_000),
    enableMultiStepAttack: bool = Query(False),
    secrets: InMemorySecrets = Depends(get_in_memory_secrets),
) -> StreamingResponse:
    # TODO: content dataset to fuzzer
    content = await file.read()  # noqa
    llm_spec = await llmSpec.read()

    scan_parameters = Scan(
        llmSpec=llm_spec,
        optimize=optimize,
        maxBudget=1000,
        enableMultiStepAttack=enableMultiStepAttack,
    )
    scan_parameters.with_secrets(secrets)
    return StreamingResponse(
        streaming_response_generator(scan_parameters), media_type="application/json"
    )
