"""Durable append-only events and per-run process locking."""

import json
import os
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(".agesec/runs")


@dataclass(frozen=True)
class Event:
    seq: int
    type: str
    time: str
    data: dict


class RunLog:
    def __init__(self, run):
        path = Path(run)
        self.path = path if path.is_dir() else ROOT / str(run)
        if not self.path.is_dir():
            raise ValueError(f"Unknown run: {run}")

    @classmethod
    def create(cls):
        ROOT.mkdir(parents=True, exist_ok=True)
        path = ROOT / (
            datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")
            + "-"
            + uuid.uuid4().hex[:10]
        )
        path.mkdir(mode=0o700)
        return cls(path)

    @contextmanager
    def lock(self):
        import fcntl

        with (self.path / ".lock").open("a") as handle:
            fcntl.flock(handle, fcntl.LOCK_EX)
            try:
                yield self
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def read(self):
        path = self.path / "events.jsonl"
        if not path.exists():
            return []
        events = [json.loads(line) for line in path.read_text().splitlines()]
        for i, event in enumerate(events):
            if event["seq"] != i:
                raise ValueError("Corrupt event sequence")
        return events

    def append(self, kind: str, data: dict, emit=None):
        event = asdict(
            Event(len(self.read()), kind, datetime.now(timezone.utc).isoformat(), data)
        )
        with (self.path / "events.jsonl").open("a") as handle:
            handle.write(json.dumps(event, ensure_ascii=True, allow_nan=False) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        if emit:
            emit(event)
        return event
