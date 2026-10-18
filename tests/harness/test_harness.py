import json
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import httpx
import pytest

from agentic_security_harness import loop, runlog
from agentic_security_harness.deciders import Decision
from agentic_security_harness.loop import Harness, replay
from agentic_security_harness.outcome import Classification, Outcome, classify
from agentic_security_harness.policy import Policy
from agentic_security_harness.report import build_report, write_report
from agentic_security_harness.runlog import RunLog


@pytest.fixture
def harness(tmp_path, monkeypatch):
    monkeypatch.setattr(runlog, "ROOT", tmp_path / "runs")
    monkeypatch.setattr(loop, "load_spec", lambda _: FakeSpec())
    monkeypatch.setattr(
        loop,
        "classify",
        lambda response, error="": Classification(
            Outcome.ERROR if error else Outcome.REFUSED, error or "refused"
        ),
    )
    spec = tmp_path / "target.http"
    spec.write_text('POST http://localhost/\n\n{"prompt":"<<PROMPT>>"}')
    (tmp_path / "prompts.csv").write_text("prompt\nfirst\nsecond\n")
    policy = tmp_path / "policy.json"
    policy.write_text(
        json.dumps(
            {
                "sources": [{"kind": "csv", "name": "prompts.csv"}],
                "rate": 100000,
                "request_cost_usd": 0.1,
                "max_attempts": 8,
            }
        )
    )

    def create(**kwargs):
        return Harness.create(str(spec), str(policy), **kwargs)

    return create


class FakeSpec:
    calls = 0

    async def probe(self, prompt):
        FakeSpec.calls += 1
        return httpx.Response(
            200,
            json={"response": "I cannot do that."},
            request=httpx.Request("POST", "http://localhost"),
        )


def test_external_resume_idempotent_and_illegal_action(harness):
    h = harness(decider="external")
    assert h.run() == 0
    before = h.log.read()
    pending = h.pending()
    resumed = Harness(h.log)
    assert resumed.step() == pending
    assert h.log.read() == before
    with pytest.raises(ValueError, match="Illegal"):
        resumed.decide(Decision("invented", "bad"))
    assert h.log.read() == before
    resumed.decide(Decision("escalate", "test converter"))
    next_h = Harness(h.log)
    assert next_h.step()["attempt"]["tier"] == "converter"
    next_h.decide(Decision("escalate", "test transcript"))
    next_h = Harness(h.log)
    p = next_h.step()
    assert "Assistant: I cannot" in p["attempt"]["prompt"]
    assert "escalate" not in p["allowed_actions"]
    next_h.decide(Decision("stop", "enough"))
    assert Harness(h.log).step() is None


def test_rules_budget_and_offline_replay(harness, monkeypatch):
    h = harness(budget_usd=0.2)
    assert h.run() == 0
    assert len(h.state.attempts) == 2
    assert h.state.cost == pytest.approx(0.2)
    monkeypatch.setattr(
        loop, "load_spec", lambda _: pytest.fail("network during replay")
    )
    received = []
    assert replay(h.log, received.append) == 0
    assert received == h.log.read()


def test_zero_budget_never_calls_target(harness):
    h = harness(budget_usd=0)
    assert h.run() == 0
    assert not h.state.attempts


def test_interrupted_delivery_not_retried(harness):
    h = harness()
    h.append("attempt_started", {"id": 0})
    h = Harness(h.log)
    assert h.step() is None
    assert h.state.finished["exit_code"] == 2
    assert not h.state.attempts


def test_error_and_finding_exit_codes(harness, monkeypatch):
    for outcome, code in [(Outcome.COMPLIED, 1), (Outcome.ERROR, 2)]:
        monkeypatch.setattr(
            loop, "classify", lambda *args, **kwargs: Classification(outcome, "test")
        )
        h = harness()
        assert h.run() == code
        assert replay(h.log) == code


def test_report_preserves_evidence_as_json(harness, monkeypatch, tmp_path):
    payload = "</script><img src=x onerror=alert(1)>\x01"

    async def probe(self, prompt):
        return httpx.Response(
            200,
            json={"response": payload},
            request=httpx.Request("POST", "http://localhost"),
        )

    monkeypatch.setattr(FakeSpec, "probe", probe)
    monkeypatch.setattr(
        loop,
        "classify",
        lambda *args, **kwargs: Classification(Outcome.COMPLIED, "review"),
    )
    h = harness()
    assert h.run() == 1
    target = tmp_path / "out" / "report.json"
    report = write_report(h.log, target)
    data = json.loads(target.read_text())
    assert data == asdict(report)
    assert data["summary"]["findings"] == 2
    assert data["findings"][0]["response"] == payload
    assert data["attacks"][0]["source"]["kind"] == "csv"
    assert list(target.parent.iterdir()) == [target]
    with pytest.raises(ValueError):
        write_report(h.log, h.log.path / "events.jsonl")


def test_incomplete_report_has_no_final_verdict(harness):
    h = harness(decider="external")
    h.run()
    report = build_report(h.log)
    assert report.status == "pending"
    assert report.exit_code is None
    with pytest.raises(ValueError, match="finished"):
        replay(h.log)


def test_classifier_mixed_and_empty():
    class Detector:
        def is_refusal(self, text):
            return "cannot" in text

    assert classify("I cannot help", detector=Detector()).outcome == "refused"
    assert (
        classify("I cannot help\n\nHere are instructions", detector=Detector()).outcome
        == "partial"
    )
    assert classify("Here are instructions", detector=Detector()).outcome == "complied"
    assert classify("").outcome == "error"


def test_policy_rejects_bad_values():
    for kwargs in (
        {"max_attempts": 0},
        {"rate": 0},
        {"rate": float("nan")},
        {"request_cost_usd": -1},
        {"rules": {"refused": ["invented"]}},
    ):
        with pytest.raises(ValueError):
            Policy(**kwargs)


def test_jev_failure_cost_is_preserved(harness, monkeypatch):
    h = harness()
    # Freeze a jev configuration without making a real remote call.
    events = h.log.read()
    events[0]["data"]["decider"] = "jev"
    events[0]["data"]["policy"]["jev_model"] = "test/model"
    events[0]["data"]["policy"]["decision_cost_usd"] = 0.2
    (h.log.path / "events.jsonl").write_text(json.dumps(events[0]) + "\n")

    def fail(*args):
        raise ValueError("remote error")

    monkeypatch.setattr(loop.JevDecider, "decide", fail)
    h = Harness(h.log)
    assert h.run() == 2
    assert h.state.cost == pytest.approx(0.3)
    assert Harness(h.log).state.cost == pytest.approx(0.3)


def test_cli_step_finished_and_illegal(harness):
    h = harness(decider="external")
    h.run()
    root = Path(__file__).resolve().parents[2]
    command = [sys.executable, "-m", "agentic_security_harness"]
    result = subprocess.run(
        command + ["step", str(h.log.path)], cwd=root, capture_output=True, text=True
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["allowed_actions"]
    result = subprocess.run(
        command + ["decide", str(h.log.path), "--action", "bad"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 2
    result = subprocess.run(
        command + ["decide", str(h.log.path), "--action", "stop"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert json.loads(result.stdout)["ok"]
    result = subprocess.run(
        command + ["step", str(h.log.path)], cwd=root, capture_output=True, text=True
    )
    assert result.returncode == 3
    assert not result.stdout


def test_cli_report_returns_json_only(harness, tmp_path):
    h = harness()
    h.run()
    target = tmp_path / "output" / "report.json"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "agentic_security_harness",
            "report",
            str(h.log.path),
            "-o",
            str(target),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == json.loads(target.read_text())
    assert list(target.parent.iterdir()) == [target]


def test_technique_provenance_is_cached(harness, monkeypatch):
    h = harness(decider="external")
    h.run()
    h.decide(Decision("escalate", "try converter"))
    pending = h.step()
    assert pending["attempt"]["technique"]["name"] == "base64"
    assert pending["attempt"]["source"]["kind"] == "csv"
    h.decide(Decision("stop", "done"))
    monkeypatch.setattr(
        loop, "prepare_prompt", lambda *args: pytest.fail("Replay executed a technique")
    )
    assert replay(h.log) == 0
