import os
from asyncio import Event, Queue

from fastapi import FastAPI

tools_inbox: Queue = Queue()
stop_event: Event = Event()
current_run: str = {"spec": "", "id": ""}
_secrets = {}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI()
    return app


def get_tools_inbox() -> Queue:
    """Get the global tools inbox queue."""
    return tools_inbox


def get_stop_event() -> Event:
    """Get the global stop event."""
    return stop_event


def get_current_run() -> str:
    """Get the current run id."""
    return current_run


def set_current_run(spec):
    """Set the current run id."""
    current_run["id"] = hash(id(spec))
    current_run["spec"] = spec
    return current_run


def get_secrets():
    return _secrets


def set_secrets(secrets):
    _secrets.update(secrets)
    expand_secrets(_secrets)
    return _secrets


def expand_secrets(secrets):
    for key in secrets:
        val = secrets[key]
        if val.startswith("$"):
            secrets[key] = os.getenv(val.strip("$"))
