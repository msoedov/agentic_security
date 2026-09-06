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
from ..http_spec import InvalidHTTPSpecError, LLMSpec
from ..primitives import LLMInfo, Scan
from ..probe_actor import fuzzer
from ..probe_data.data import parse_csv_content

router = APIRouter()


@router.post("/verify")
async def verify(
    info: LLMInfo, secrets: InMemorySecrets = Depends(get_in_memory_secrets)
) -> dict[str, int | str | float]:
    logger.info("verify: checking LLM spec connectivity")
    spec = LLMSpec.from_string(info.spec)
    try:
        r = await spec.verify()
    except InvalidHTTPSpecError as e:
        logger.warning("verify: invalid HTTP spec: %s", e)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("verify: unexpected failure")
        raise HTTPException(status_code=400, detail=str(e))

    if r.status_code >= 400:
        logger.warning("verify: upstream returned HTTP %s", r.status_code)
        raise HTTPException(status_code=r.status_code, detail=r.text)
    logger.info(
        "verify: success status=%s elapsed=%.2fs",
        r.status_code,
        r.elapsed.total_seconds(),
    )
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
    logger.info(
        "scan: starting stream maxBudget=%s optimize=%s multiStep=%s",
        scan_parameters.maxBudget,
        scan_parameters.optimize,
        scan_parameters.enableMultiStepAttack,
    )
    scan_parameters.with_secrets(secrets)
    return StreamingResponse(
        streaming_response_generator(scan_parameters), media_type="application/json"
    )


@router.post("/stop")
async def stop_scan() -> dict[str, str]:
    logger.info("stop: scan stop requested")
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
    content = await file.read()
    llm_spec = await llmSpec.read()

    # Parse the uploaded CSV into an inline dataset
    inline_datasets = []
    try:
        dataset = parse_csv_content(content)
        inline_datasets.append(
            {"name": dataset.dataset_name, "prompts": dataset.prompts}
        )
    except ValueError as e:
        logger.warning("scan-csv: failed to parse CSV upload: %s", e)
        raise HTTPException(status_code=400, detail=str(e)) from e

    logger.info(
        "scan-csv: starting stream rows=%s maxBudget=%s optimize=%s",
        len(inline_datasets[0]["prompts"]) if inline_datasets else 0,
        maxBudget,
        optimize,
    )
    scan_parameters = Scan(
        llmSpec=llm_spec,
        optimize=optimize,
        maxBudget=maxBudget,
        enableMultiStepAttack=enableMultiStepAttack,
        inline_datasets=inline_datasets,
    )
    scan_parameters.with_secrets(secrets)
    return StreamingResponse(
        streaming_response_generator(scan_parameters), media_type="application/json"
    )
