"""Structured evidence for agents and CI; presentation belongs to the consumer."""

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from agentic_security_harness.loop import Harness


@dataclass(frozen=True)
class Summary:
    attempts: int
    findings: int
    outcomes: dict[str, int]
    cost_usd: float
    duration_seconds: float


@dataclass(frozen=True)
class AttackReport:
    attack_id: str
    source: dict
    attempts: list[dict]
    decisions: list[dict]


@dataclass(frozen=True)
class Report:
    schema_version: int
    run_id: str
    status: str
    exit_code: int | None
    stop_reason: str | None
    summary: Summary
    findings: list[dict]
    attacks: list[AttackReport]
    events: list[dict]
    limitations: list[str]


def build_report(log) -> Report:
    harness = Harness(log)
    events = log.read()
    state = harness.state
    findings = [a for a in state.attempts if a["outcome"] in ("partial", "complied")]
    counts = {
        o: sum(a["outcome"] == o for a in state.attempts)
        for o in ("refused", "partial", "complied", "error")
    }
    duration = (
        datetime.fromisoformat(events[-1]["time"])
        - datetime.fromisoformat(events[0]["time"])
    ).total_seconds()
    attacks = []
    for attack in harness.attacks:
        attempts = [a for a in state.attempts if a["attack_id"] == attack.id]
        ids = {a["id"] for a in attempts}
        attacks.append(
            AttackReport(
                attack.id,
                attack.source,
                attempts,
                [d for d in state.decisions if d["attempt_id"] in ids],
            )
        )
    return Report(
        schema_version=1,
        run_id=log.path.name,
        status=(
            "finished"
            if state.finished
            else "interrupted" if state.in_flight else "pending"
        ),
        exit_code=state.finished["exit_code"] if state.finished else None,
        stop_reason=state.finished["reason"] if state.finished else None,
        summary=Summary(
            len(state.attempts), len(findings), counts, state.cost, duration
        ),
        findings=findings,
        attacks=attacks,
        events=events,
        limitations=[
            "Findings are refusal-classifier signals requiring review, not verified exploitation.",
            "Costs use configured estimates as a floor; provider charges may differ.",
            "OWASP mappings describe attack objectives, not complete Top 10 coverage.",
        ],
    )


def write_report(log, output=None) -> Report:
    report = build_report(log)
    target = Path(output) if output else log.path / "report.json"
    if target.resolve() in {
        (log.path / name).resolve() for name in ("events.jsonl", "spec.http", ".lock")
    }:
        raise ValueError("Report output must not overwrite run data")
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(asdict(report), indent=2, ensure_ascii=True, allow_nan=False) + "\n"
    )
    return report
