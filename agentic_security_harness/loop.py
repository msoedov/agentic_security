"""Attempt → classify → decide, reconstructed from durable events on each command."""

import asyncio
import math
import os
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from agentic_security_harness.deciders import Decision, JevDecider, RulesDecider
from agentic_security_harness.outcome import classify
from agentic_security_harness.policy import Policy
from agentic_security_harness.runlog import RunLog
from agentic_security_harness.tiers import Attack, TIERS, load_attacks, prepare_prompt


@dataclass
class State:
    attack: int = 0
    tier: int = 0
    turn: int = 0
    attempts: list[dict] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    pending: bool = False
    in_flight: bool = False
    stopped: bool = False
    finished: dict | None = None
    cost: float = 0.0

    def apply(self, event):
        data = event["data"]
        match event["type"]:
            case "attempt_started":
                if self.in_flight or self.pending or self.finished:
                    raise ValueError("Invalid attempt transition")
                self.in_flight = True
            case "attempt":
                if not self.in_flight:
                    raise ValueError("Attempt has no start event")
                self.in_flight = False
                self.attempts.append(data)
                self.cost += data["cost_usd"]
                self.turn += 1
                self.pending = True
            case "decision":
                if not self.pending:
                    raise ValueError("Decision has no pending attempt")
                self.decisions.append(data)
                self.cost += data["cost_usd"]
                self.pending = False
                match data["action"]:
                    case "escalate":
                        self.tier = data["next_tier"]
                        self.turn = 0
                    case "switch":
                        self.attack += 1
                        self.tier = self.turn = 0
                    case "stop":
                        self.stopped = True
                    case "continue":
                        pass
                    case _:
                        raise ValueError("Unknown action")
            case "decision_error":
                self.cost += data["cost_usd"]
            case "finished":
                self.finished = data


def result_code(state):
    if state.in_flight or any(a["outcome"] == "error" for a in state.attempts):
        return 2
    return int(any(a["outcome"] in ("partial", "complied") for a in state.attempts))


def extract_response(response):
    response.raise_for_status()
    try:
        data = response.json()
    except ValueError:
        return response.text, None
    if isinstance(data, dict):
        cost = data.get("usage", {}).get("cost")
        if "choices" in data:
            text = data["choices"][0]["message"].get("content")
            if not isinstance(text, str):
                raise ValueError("Expected text content in response")
            return text, cost
        for key in ("response", "output", "text", "content"):
            if isinstance(data.get(key), str):
                return data[key], cost
        raise ValueError(
            "Unsupported JSON response; expected choices, response, output, text or content"
        )
    if isinstance(data, str):
        return data, None
    raise ValueError("Unsupported response format")


def load_spec(path):
    from agentic_security.http_spec import LLMSpec

    text = Path(path).read_text()

    def expand(match):
        key = match[1]
        if key not in os.environ:
            raise ValueError(f"Missing environment variable: {key}")
        return os.environ[key]

    text = re.sub(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}", expand, text)
    spec = LLMSpec.from_string(text)
    if "<<PROMPT>>" not in spec.body:
        raise ValueError("HTTP spec body must contain <<PROMPT>>")
    if spec.has_files or spec.has_image or spec.has_audio:
        raise ValueError("Harness currently supports text HTTP specs only")
    return spec


class Harness:
    def __init__(self, log: RunLog, emit=None):
        self.log, self.emit = log, emit
        events = log.read()
        if not events or events[0]["type"] != "created":
            raise ValueError("Run has no configuration")
        self.config = events[0]["data"]
        self.policy = Policy(**self.config["policy"])
        self.attacks = [Attack(**a) for a in self.config["attacks"]]
        self.state = State()
        for event in events[1:]:
            if event["type"] == "decision":
                if event["data"]["action"] not in self.pending()["allowed_actions"]:
                    raise ValueError("Logged decision violates policy")
            self.state.apply(event)

    @classmethod
    def create(
        cls, spec, policy="default", decider="rules", seed=0, budget_usd=None, emit=None
    ):
        if decider not in ("rules", "jev", "external"):
            raise ValueError("Unknown decider")
        p = Policy.load(policy)
        if budget_usd is not None:
            budget_usd = float(budget_usd)
            if not math.isfinite(budget_usd) or budget_usd < 0:
                raise ValueError("budget_usd must be finite and nonnegative")
            if p.request_cost_usd <= 0 or (
                decider == "jev" and p.decision_cost_usd <= 0
            ):
                raise ValueError(
                    "Dollar budgets require positive request/jev decision cost estimates in policy"
                )
        if decider == "jev":
            JevDecider(p.jev_model)
            if not os.environ.get("OPENROUTER_API_KEY"):
                raise ValueError("OPENROUTER_API_KEY is required for jev")
        load_spec(spec)
        attacks = load_attacks(p, int(seed))
        log = RunLog.create()
        # Store the template, not expanded environment secrets; owner-only run directory.
        (log.path / "spec.http").write_text(Path(spec).read_text())
        log.append(
            "created",
            {
                "version": 1,
                "run_id": log.path.name,
                "policy": asdict(p),
                "attacks": [asdict(a) for a in attacks],
                "decider": decider,
                "seed": int(seed),
                "budget_usd": budget_usd,
            },
            emit,
        )
        return cls(log, emit)

    def append(self, kind, data):
        event = self.log.append(kind, data, self.emit)
        self.state.apply(event)

    def can_spend(self, amount):
        budget = self.config["budget_usd"]
        return budget is None or self.state.cost + amount <= budget + 1e-12

    def pending(self):
        s = self.state
        if not s.pending:
            raise ValueError("No pending decision")
        allowed = self.policy.allowed(
            s.attempts[-1]["outcome"], s.tier, s.turn, s.attack + 1 < len(self.attacks)
        )
        if len(s.attempts) >= self.policy.max_attempts or not self.can_spend(
            self.policy.request_cost_usd
        ):
            allowed = ["stop"]
        return {
            "run_id": self.log.path.name,
            "attempt": s.attempts[-1],
            "outcome": s.attempts[-1]["outcome"],
            "history_summary": {
                "attempts": len(s.attempts),
                "cost_usd": s.cost,
                "outcomes": {
                    o: sum(a["outcome"] == o for a in s.attempts)
                    for o in ("refused", "partial", "complied", "error")
                },
                "recent_decisions": s.decisions[-5:],
            },
            "allowed_actions": allowed,
        }

    def finish(self, reason, code=None):
        if not self.state.finished:
            self.append(
                "finished",
                {
                    "reason": reason,
                    "exit_code": result_code(self.state) if code is None else code,
                    "cost_usd": self.state.cost,
                },
            )

    def decide(self, decision: Decision, source="external"):
        if decision.action not in self.pending()["allowed_actions"]:
            raise ValueError(f"Illegal action: {decision.action}")
        if not math.isfinite(decision.cost_usd) or decision.cost_usd < 0:
            raise ValueError("Invalid decision cost")
        self.append(
            "decision",
            {
                **asdict(decision),
                "source": source,
                "attempt_id": self.state.attempts[-1]["id"],
                "next_tier": (
                    self.policy.next_tier(self.state.tier)
                    if decision.action == "escalate"
                    else self.state.tier
                ),
            },
        )
        if self.state.stopped:
            self.finish("stop decision")

    async def attempt(self):
        from agentic_security.executor.rate_limiter import TokenBucketRateLimiter
        from agentic_security.executor.circuit_breaker import CircuitBreaker

        s = self.state
        breaker = CircuitBreaker()
        for a in s.attempts:
            (
                breaker.record_failure()
                if a["outcome"] == "error"
                else breaker.record_success()
            )
        if breaker.is_open():
            self.finish("circuit breaker open", 2)
            return
        limiter = TokenBucketRateLimiter(self.policy.rate, 1)
        # Persist rate spacing across step processes (including time spent idle).
        starts = [e for e in self.log.read() if e["type"] == "attempt_started"]
        if starts:
            from datetime import datetime

            elapsed = (
                time.time() - datetime.fromisoformat(starts[-1]["time"]).timestamp()
            )
            await asyncio.sleep(max(0, 1 / self.policy.rate - elapsed))
        await limiter.acquire()
        attack = self.attacks[s.attack]
        prompt, technique = attack.prompt, {}
        attempt_id = len(s.attempts)
        self.append("attempt_started", {"id": attempt_id, "attack_id": attack.id})
        start = time.monotonic()
        response, error, cost = "", "", self.policy.request_cost_usd
        estimated = True
        try:
            prepared = prepare_prompt(
                attack, s.tier, s.turn, s.attempts, self.policy, self.config["seed"]
            )
            prompt, technique = prepared.prompt, prepared.technique
            spec = load_spec(self.log.path / "spec.http")
            response, actual = extract_response(await spec.probe(prompt))
            if actual is not None:
                actual = float(actual)
                if not math.isfinite(actual) or actual < 0:
                    raise ValueError("Invalid target cost")
                cost, estimated = max(cost, actual), False
            classification = classify(response)
        except Exception as exc:
            # Exception messages can contain authorization headers/URLs from HTTP clients.
            error = type(exc).__name__
            classification = classify("", error=error)
        self.append(
            "attempt",
            {
                "id": attempt_id,
                "attack_id": attack.id,
                "tier": TIERS[s.tier],
                "prompt": prompt,
                "response": response,
                "outcome": classification.outcome,
                "reason": classification.reason,
                "error": error,
                "cost_usd": cost,
                "cost_estimated": estimated,
                "duration_seconds": time.monotonic() - start,
                "owasp": list(attack.owasp),
                "source": attack.source,
                "technique": technique,
            },
        )

    def step(self):
        s = self.state
        if s.finished:
            return None
        if s.in_flight:
            self.finish("Interrupted request; delivery unknown; not retried", 2)
            return None
        if s.pending:
            return self.pending()
        if (
            s.stopped
            or s.attack >= len(self.attacks)
            or len(s.attempts) >= self.policy.max_attempts
        ):
            self.finish("complete")
            return None
        if not self.can_spend(self.policy.request_cost_usd):
            self.finish("budget exhausted")
            return None
        asyncio.run(self.attempt())
        return self.pending() if s.pending else None

    def run(self):
        while pending := self.step():
            if self.config["decider"] == "external":
                return 0  # paused; final status is available via ls/replay/report
            source = self.config["decider"]
            if pending["allowed_actions"] == ["stop"]:
                self.decide(Decision("stop", "Policy limit reached"), "rules")
                continue
            if source == "rules":
                self.decide(RulesDecider().decide(pending), source)
                continue
            if not self.can_spend(self.policy.decision_cost_usd):
                self.decide(Decision("stop", "Decision budget exhausted"), "rules")
                continue
            try:
                decision = JevDecider(self.policy.jev_model).decide(pending)
                cost = max(self.policy.decision_cost_usd, decision.cost_usd)
                self.decide(Decision(decision.action, decision.reason, cost), source)
            except Exception as exc:
                # A failed/invalid paid decision still reserves its estimated cost.
                self.append(
                    "decision_error",
                    {
                        "error": type(exc).__name__,
                        "cost_usd": self.policy.decision_cost_usd,
                    },
                )
                self.finish("Decider failed", 2)
        return self.state.finished["exit_code"]


def replay(log, emit=None):
    """Re-execute the state machine using recorded attempts and decisions, offline."""
    harness = Harness(log)
    if not harness.state.finished:
        raise ValueError("Replay requires a finished run")
    for event in log.read():
        if emit:
            emit(event)
    return harness.state.finished["exit_code"]
