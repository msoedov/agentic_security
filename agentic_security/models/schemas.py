import os

from pydantic import BaseModel, Field


class Settings:
    MAX_BUDGET = 1000
    MAX_DATASETS = 10
    RATE_LIMIT = "100/minute"
    DISABLE_TELEMETRY = os.getenv("DISABLE_TELEMETRY", False)
    FEATURE_PROXY = False


class LLMInfo(BaseModel):
    spec: str


class Scan(BaseModel):
    llmSpec: str
    maxBudget: int
    datasets: list[dict] = []
    optimize: bool = False
    enableMultiStepAttack: bool = False


class ScanResult(BaseModel):
    module: str
    tokens: float | int
    cost: float
    progress: float
    status: bool = False
    failureRate: float = 0.0

    @classmethod
    def status_msg(cls, msg: str) -> str:
        return cls(
            module=msg,
            tokens=0,
            cost=0,
            progress=0,
            failureRate=0,
            status=True,
        ).model_dump_json()


class Probe(BaseModel):
    prompt: str


class Message(BaseModel):
    role: str
    content: str


class CompletionRequest(BaseModel):
    """Model for completion requests."""

    model: str
    messages: list[Message]
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    top_p: float = Field(default=1.0, ge=0.0, le=1.0)
    n: int = Field(default=1, ge=1, le=10)
    stop: list[str] | None = None
    max_tokens: int = Field(default=100, ge=1, le=4096)
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)


class Table(BaseModel):
    table: list[dict]
