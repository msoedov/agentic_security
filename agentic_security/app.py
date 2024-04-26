import random
import sys
from datetime import datetime
from pathlib import Path

from fastapi import BackgroundTasks, FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from loguru import logger
from pydantic import BaseModel

from .http_spec import LLMSpec
from .probe_actor import fuzzer
from .probe_actor.refusal import REFUSAL_MARKS
from .probe_data import REGISTRY
from .report_chart import plot_security_report

logger.remove(0)
logger.add(
    sys.stderr,
    format="<green>[{level}]</green> <blue>{time:YYYY-MM-DD HH:mm:ss.SS}</blue> | <cyan>{module}:{function}:{line}</cyan> | <white>{message}</white>",
    colorize=True,
    level="INFO",
)


# Create the FastAPI app instance
app = FastAPI()
origins = [
    "*",
]

# Middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)


@app.get("/")
async def root():
    agentic_security_path = Path(__file__).parent
    return FileResponse(f"{agentic_security_path}/static/index.html")


class LLMInfo(BaseModel):
    spec: str


@app.post("/verify")
async def verify(info: LLMInfo):

    spec = LLMSpec.from_string(info.spec)
    r = await spec.probe("test")
    if r.status_code >= 400:
        raise HTTPException(status_code=r.status_code, detail=r.text)
    return dict(
        status_code=r.status_code,
        body=r.text,
        elapsed=r.elapsed.total_seconds(),
        timestamp=datetime.now().isoformat(),
    )


class Scan(BaseModel):
    llmSpec: str
    maxBudget: int
    datasets: list[dict] = []


class ScanResult(BaseModel):
    module: str
    tokens: int
    cost: float
    progress: float
    failureRate: float = 0.0


def streaming_response_generator(scan_parameters: Scan):
    # The generator function for StreamingResponse
    request_factory = LLMSpec.from_string(scan_parameters.llmSpec)

    async def _gen():
        async for scan_result in fuzzer.perform_scan(
            request_factory=request_factory,
            max_budget=scan_parameters.maxBudget,
            datasets=scan_parameters.datasets,
        ):
            yield scan_result + "\n"  # Adding a newline for separation

    return _gen()


@app.post("/scan")
async def scan(scan_parameters: Scan, background_tasks: BackgroundTasks):

    # Initiates streaming of scan results
    return StreamingResponse(
        streaming_response_generator(scan_parameters), media_type="application/json"
    )


class Probe(BaseModel):
    prompt: str


@app.post("/v1/self-probe")
def self_probe(probe: Probe):
    refuse = random.random() < 0.2
    message = random.choice(REFUSAL_MARKS) if refuse else "This is a test!"
    message = probe.prompt + " " + message
    return {
        "id": "chatcmpl-abc123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-3.5-turbo-0613",
        "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
        "choices": [
            {
                "message": {"role": "assistant", "content": message},
                "logprobs": None,
                "finish_reason": "stop",
                "index": 0,
            }
        ],
    }


@app.get("/v1/data-config")
def data_config():
    return [m for m in REGISTRY]


@app.get("/failures")
async def failures_csv():
    if not Path("failures.csv").exists():
        return {"error": "No failures found"}
    return FileResponse("failures.csv")


class Table(BaseModel):
    table: list[dict]


@app.post("/plot.jpeg", response_class=Response)
async def get_plot(table: Table):
    buf = plot_security_report(table.table)
    return StreamingResponse(buf, media_type="image/jpeg")
