import os
from asyncio import Event, Queue
from typing import TypedDict

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from agentic_security.http_spec import LLMSpec


class CurrentRun(TypedDict):
    id: int | None
    spec: LLMSpec | None


tools_inbox: Queue = Queue()
stop_event: Event = Event()
current_run: CurrentRun = {"spec": None, "id": None}
_secrets: dict[str, str | None] = {}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(default_response_class=ORJSONResponse)
    return app


def get_tools_inbox() -> Queue:
    """Get the global tools inbox queue."""
    return tools_inbox


def get_stop_event() -> Event:
    """Get the global stop event."""
    return stop_event


def get_current_run() -> CurrentRun:
    """Get the current run id."""
    return current_run


def set_current_run(spec: LLMSpec) -> CurrentRun:
    """Set the current run metadata based on a spec instance."""
    current_run["id"] = hash(id(spec))
    current_run["spec"] = spec
    return current_run


def get_secrets() -> dict[str, str | None]:
    return _secrets


def set_secrets(secrets: dict[str, str | None]) -> dict[str, str | None]:
    expanded = dict(secrets)
    expand_secrets(expanded)
    _secrets.update(expanded)
    return _secrets


def expand_secrets(secrets: dict[str, str | None]) -> None:
    for key, val in secrets.items():
        if isinstance(val, str) and val.startswith("$"):
            env_name = val.strip("$")
            secrets[key] = os.getenv(env_name) if env_name else None
