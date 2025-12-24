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
_secrets: dict[str, str] = {}


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


def get_secrets() -> dict[str, str]:
    return _secrets


def set_secrets(secrets: dict[str, str]) -> dict[str, str]:
    _secrets.update(secrets)
    expand_secrets(_secrets)
    return _secrets


def expand_secrets(secrets: dict[str, str]) -> None:
    for key in secrets:
        val = secrets[key]
        if val.startswith("$"):
            env_value = os.getenv(val.strip("$"))
            if env_value is not None:
                secrets[key] = env_value
            else:
                secrets[key] = None
