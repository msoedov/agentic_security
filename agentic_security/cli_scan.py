"""Stateless command-line scanning helpers."""

from __future__ import annotations

import asyncio
import copy
import json
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from rich.console import Console

from agentic_security.http_spec import LLMSpec
from agentic_security.primitives import Scan, ScanResult

EXIT_OK = 0
EXIT_FINDINGS = 1
EXIT_ERROR = 2


class CLIUsageError(ValueError):
    """Raised when a scan command cannot be constructed from its arguments."""


def load_spec(spec: str, stdin: TextIO | None = None) -> str:
    """Load an HTTP spec from a path, standard input, or an inline argument."""
    if spec == "-":
        content = (stdin or sys.stdin).read()
    else:
        candidate = Path(spec)
        try:
            content = (
                candidate.read_text(encoding="utf-8") if candidate.is_file() else spec
            )
        except OSError as exc:
            raise CLIUsageError(
                f"Could not read HTTP spec from {candidate}: {exc}"
            ) from exc

    if not content.strip():
        raise CLIUsageError("HTTP spec is empty.")
    return content


def select_datasets(dataset: str | Sequence[str]) -> list[dict]:
    """Resolve one or more comma-separated registry names."""
    from agentic_security.probe_data import REGISTRY

    values = [dataset] if isinstance(dataset, str) else list(dataset)
    names = [
        name.strip()
        for value in values
        for name in str(value).split(",")
        if name.strip()
    ]
    if not names:
        raise CLIUsageError("At least one --dataset value is required.")

    registry = {item["dataset_name"]: item for item in REGISTRY}
    unknown = [name for name in names if name not in registry]
    if unknown:
        joined = ", ".join(unknown)
        raise CLIUsageError(
            f"Unknown dataset: {joined}. Run `agentic_security ls` to list choices."
        )

    if "AgenticBackend" in names:
        raise CLIUsageError(
            "AgenticBackend requires the web server and cannot be used by stateless scan."
        )

    selected = []
    for name in dict.fromkeys(names):
        item = copy.deepcopy(registry[name])
        item["selected"] = True
        selected.append(item)
    return selected


def _move_logs_to(stderr: TextIO) -> None:
    """Keep library logs away from the JSON-lines stream."""
    from agentic_security import logutils

    root_logger = logging.getLogger(logutils.LOGGER_NAME)
    for handler in root_logger.handlers:
        if hasattr(handler, "console"):
            handler.console = Console(file=stderr, color_system=None)
        elif isinstance(handler, logging.StreamHandler):
            handler.setStream(stderr)


def _scan_events(**kwargs):
    """Import the scan engine only after stateless mode is enabled."""
    from agentic_security.probe_actor import fuzzer

    return fuzzer.scan_router(**kwargs)


async def stream_scan(
    *,
    spec_text: str,
    datasets: list[dict],
    max_budget: int,
    max_th: float,
    optimize: bool,
    artifacts_dir: str | None,
    stdout: TextIO,
) -> int:
    """Run a scan and emit one valid JSON object per output line."""
    request_factory = LLMSpec.from_string(spec_text)
    scan_parameters = Scan(
        llmSpec=spec_text,
        maxBudget=max_budget,
        datasets=datasets,
        optimize=optimize,
    )

    final_failure_rates: dict[str, float] = {}
    runtime_failed = False
    completion_event: dict | None = None
    events = _scan_events(
        request_factory=request_factory,
        scan_parameters=scan_parameters,
        artifacts_dir=artifacts_dir,
    )
    async for raw_event in events:
        event = json.loads(raw_event)
        module = str(event.get("module", ""))
        if event.get("status") and module == "Scan completed.":
            completion_event = event
            continue

        stdout.write(json.dumps(event, separators=(",", ":")) + "\n")
        stdout.flush()

        if event.get("status"):
            runtime_failed = runtime_failed or module.startswith("Scan failed:")
        elif module:
            final_failure_rates[module] = float(event.get("failureRate", 0))

    if not runtime_failed and not final_failure_rates:
        runtime_failed = True
        error = json.loads(ScanResult.status_msg("Scan failed: no dataset results."))
        stdout.write(json.dumps(error, separators=(",", ":")) + "\n")

    if completion_event is not None:
        stdout.write(json.dumps(completion_event, separators=(",", ":")) + "\n")
    stdout.flush()

    if runtime_failed:
        return EXIT_ERROR
    if any(rate > max_th * 100 for rate in final_failure_rates.values()):
        return EXIT_FINDINGS
    return EXIT_OK


def run_scan_command(
    *,
    spec: str,
    dataset: str | Sequence[str],
    max_budget: int = 1_000,
    max_th: float = 0.3,
    optimize: bool = False,
    artifacts_dir: str | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Validate CLI inputs, execute the scan, and return a process exit code."""
    stdout = stdout or sys.stdout
    stderr = stderr or sys.stderr
    _move_logs_to(stderr)
    previous_mode = os.environ.get("AGENTIC_SECURITY_STATELESS")
    os.environ["AGENTIC_SECURITY_STATELESS"] = "1"

    try:
        if max_budget <= 0:
            raise CLIUsageError("--max-budget must be greater than zero.")
        if not 0 <= max_th <= 1:
            raise CLIUsageError("--max-th must be between 0 and 1.")

        spec_text = load_spec(spec, stdin)
        datasets = select_datasets(dataset)
        return asyncio.run(
            stream_scan(
                spec_text=spec_text,
                datasets=datasets,
                max_budget=max_budget,
                max_th=max_th,
                optimize=optimize,
                artifacts_dir=artifacts_dir,
                stdout=stdout,
            )
        )
    except KeyboardInterrupt:
        stderr.write("Scan interrupted.\n")
        return 130
    except Exception as exc:
        stderr.write(f"Scan error: {exc}\n")
        return EXIT_ERROR
    finally:
        if previous_mode is None:
            os.environ.pop("AGENTIC_SECURITY_STATELESS", None)
        else:
            os.environ["AGENTIC_SECURITY_STATELESS"] = previous_mode
