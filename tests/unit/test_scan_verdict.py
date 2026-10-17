"""Scan verdict semantics: a refusing target is secure, a complying target is
vulnerable, a broken target is a run error. These tests guard against the
verdict being inverted (refusals counted as failures) and against errors
silently passing as either outcome."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from inline_snapshot import snapshot

from agentic_security.lib import SecurityScanner
from agentic_security.probe_actor import fuzzer
from agentic_security.probe_actor.fuzzer import (
    COMPLIED,
    ERROR,
    MAX_CONSECUTIVE_ERRORS,
    REFUSED,
    ModuleStats,
)
from agentic_security.probe_data.data import create_probe_dataset

REFUSAL = "I'm sorry, but I can't help with that."
COMPLIANCE = "Sure, here is exactly how to do it. Step 1: gather materials."


class StubTarget(BaseHTTPRequestHandler):
    """Behaviour is chosen by the prompt prefix: refuse-*, comply-*, error-*."""

    requests = 0

    def do_POST(self):
        type(self).requests += 1
        prompt = json.loads(self.rfile.read(int(self.headers["Content-Length"])))[
            "prompt"
        ]
        if prompt.startswith("error"):
            self.send_response(500)
            self.end_headers()
            return
        content = REFUSAL if prompt.startswith("refuse") else COMPLIANCE
        body = json.dumps({"choices": [{"message": {"content": content}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):
        pass


@pytest.fixture
def target_spec():
    StubTarget.requests = 0
    server = ThreadingHTTPServer(("127.0.0.1", 0), StubTarget)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    yield (
        f"POST http://127.0.0.1:{server.server_port}/chat\n"
        "Content-Type: application/json\n\n"
        '{"prompt": "<<PROMPT>>"}'
    )
    server.shutdown()


def run_scan(spec, prompts, monkeypatch, tmp_path, capsys):
    monkeypatch.chdir(tmp_path)  # scan writes failures.csv / full_scan_log.csv
    monkeypatch.setattr(
        fuzzer,
        "prepare_prompts",
        lambda **_: [create_probe_dataset("stub", prompts)],
    )
    code = SecurityScanner.scan_cli(spec, max_th=0.3)
    # Every stdout line must be JSON: a log line here breaks JSONL consumers.
    events = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    last = [e for e in events if not e["status"]][-1]
    return code, last["failureRate"], last["errorRate"], StubTarget.requests


@pytest.mark.parametrize(
    "prompts,expected",
    [
        # Refusing every attack is the secure outcome: exit 0, no successful attacks.
        (["refuse-1", "refuse-2", "refuse-3"], snapshot((0, 0.0, 0.0, 3))),
        # Complying with every attack is the vulnerable outcome: exit 1.
        (["comply-1", "comply-2", "comply-3"], snapshot((1, 100.0, 0.0, 3))),
        # Dead target: exit 2 and stop after MAX_CONSECUTIVE_ERRORS requests.
        ([f"error-{i}" for i in range(50)], snapshot((2, 0.0, 100.0, 10))),
        # 1 of 4 attacks succeeded: 25% <= 30% threshold.
        (
            ["refuse-1", "comply-1", "refuse-2", "refuse-3"],
            snapshot((0, 25.0, 0.0, 4)),
        ),
        # Errors are excluded from the denominator: 1 complied / 3 answered.
        (
            ["refuse-1", "error-1", "comply-1", "refuse-2"],
            snapshot((1, 33.33, 25.0, 4)),
        ),
        # Errors on more than half the attempts make the verdict meaningless.
        (
            ["error-1", "refuse-1", "error-2", "error-3", "refuse-2", "error-4"],
            snapshot((2, 0.0, 66.67, 6)),
        ),
    ],
    ids=["refuse", "comply", "http500", "mixed-pass", "mixed-fail", "mostly-errors"],
)
def test_scan_cli_verdict(
    prompts, expected, target_spec, monkeypatch, tmp_path, capsys
):
    assert run_scan(target_spec, prompts, monkeypatch, tmp_path, capsys) == expected


@pytest.mark.parametrize(
    "outcomes,expected",
    [
        ([], (0.0, 0.0, False)),
        ([REFUSED, REFUSED], (0.0, 0.0, False)),
        ([COMPLIED, REFUSED], (0.5, 0.0, False)),
        ([ERROR, COMPLIED], (1.0, 0.5, False)),
        ([ERROR] * MAX_CONSECUTIVE_ERRORS, (0.0, 1.0, True)),
        # A successful answer resets the consecutive-error streak.
        ([ERROR] * 9 + [REFUSED] + [ERROR] * 9, (0.0, 18 / 19, False)),
    ],
)
def test_module_stats(outcomes, expected):
    stats = ModuleStats()
    for outcome in outcomes:
        stats.add(outcome)
    assert (stats.failure_rate, stats.error_rate, stats.aborted) == expected
