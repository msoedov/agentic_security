from asyncio import Event, Queue
from fastapi import FastAPI

tools_inbox: Queue = Queue()
stop_event: Event = Event()


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
