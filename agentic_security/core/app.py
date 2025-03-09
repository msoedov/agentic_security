import os
from asyncio import Event, Queue

from fastapi import FastAPI
from fastapi.responses import ORJSONResponse

from agentic_security.http_spec import LLMSpec
from typing import Any, Dict

tools_inbox: Queue = Queue()
stop_event: Event = Event()
current_run: str = {"spec": "", "id": ""}
_secrets: dict[str, str] = {}

current_run: Dict[str, int | LLMSpec] = {
    "spec": "", 
    "id": ""
}

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


def get_current_run() -> Dict[str, int | LLMSpec]:
    """Get the current run id."""
    return current_run


def set_current_run(spec : LLMSpec) -> Dict[str, int | LLMSpec]:
    """Set the current run id."""
    current_run["id"] = hash(id(spec))
    current_run["spec"] = spec
    return current_run


def get_secrets() -> dict[str, str]:
    return _secrets


def set_secrets(secrets : dict[str, str]) -> dict[str, str]:
    _secrets.update(secrets)
    expand_secrets(_secrets)
    return _secrets


def expand_secrets(secrets : dict[str, str]) -> None:
    for key in secrets:
        val = secrets[key]
        if val.startswith("$"):
            secrets[key] = os.getenv(val.strip("$"))
