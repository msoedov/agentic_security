"""Policy owns legal transitions; deciders can only choose within them."""

import json
import math
from dataclasses import dataclass, field
from typing import Literal, get_args
from pathlib import Path
from agentic_security_harness.references import Source, Technique

Action = Literal["continue", "escalate", "switch", "stop"]


@dataclass
class Policy:
    max_attempts: int = 30
    max_per_tier: int = 2
    rate: float = 1.0
    request_cost_usd: float = 0.0
    decision_cost_usd: float = 0.0
    jev_model: str = ""
    sources: list[Source] = field(
        default_factory=lambda: [Source("dataset", "harness/smoke")]
    )
    converters: list[Technique] = field(
        default_factory=lambda: [
            Technique("builtin", "base64"),
            Technique("builtin", "fictional"),
        ]
    )
    strategies: list[Technique] = field(
        default_factory=lambda: [Technique("builtin", "transcript")]
    )
    rules: dict[str, list[str]] = field(
        default_factory=lambda: {
            "refused": ["escalate", "continue", "switch", "stop"],
            "partial": ["continue", "escalate", "switch", "stop"],
            "complied": ["switch", "stop"],
            "error": ["stop"],
        }
    )

    def __post_init__(self):
        if type(self.max_attempts) is not int or self.max_attempts < 1:
            raise ValueError("max_attempts must be a positive integer")
        if type(self.max_per_tier) is not int or self.max_per_tier < 1:
            raise ValueError("max_per_tier must be a positive integer")
        if not math.isfinite(self.rate) or self.rate <= 0:
            raise ValueError("rate must be positive and finite")
        for value in (self.request_cost_usd, self.decision_cost_usd):
            if not math.isfinite(value) or value < 0:
                raise ValueError("cost estimates must be finite and nonnegative")
        if set(self.rules) != {"refused", "partial", "complied", "error"}:
            raise ValueError("rules must cover every outcome")
        for actions in self.rules.values():
            if (
                not actions
                or any(a not in get_args(Action) for a in actions)
                or "stop" not in actions
            ):
                raise ValueError("Every rule must contain legal actions including stop")
        self.sources = [Source(**s) if isinstance(s, dict) else s for s in self.sources]
        self.converters = [
            Technique(**t) if isinstance(t, dict) else t for t in self.converters
        ]
        self.strategies = [
            Technique(**t) if isinstance(t, dict) else t for t in self.strategies
        ]
        if not self.sources or not all(isinstance(s, Source) for s in self.sources):
            raise ValueError(
                "sources must contain typed dataset, csv, or module references"
            )
        for references, names in (
            (self.converters, {"base64", "fictional"}),
            (self.strategies, {"transcript"}),
        ):
            for ref in references:
                if not isinstance(ref, Technique) or (
                    ref.kind == "builtin" and ref.name not in names
                ):
                    raise ValueError("Unknown technique reference")

    def next_tier(self, tier):
        return next(
            (
                i
                for i in (1, 2)
                if i > tier and (self.converters if i == 1 else self.strategies)
            ),
            None,
        )

    @classmethod
    def load(cls, value: str):
        if value in ("default", "ci"):
            return cls(max_attempts=12 if value == "ci" else 30)
        data = json.loads(Path(value).read_text())
        if "prompts" in data or "datasets" in data:
            raise ValueError("Use typed sources references instead of prompts/datasets")
        policy = cls(**data)
        policy.sources = [
            (
                Source(
                    s.kind,
                    str((Path(value).resolve().parent / s.name).resolve()),
                    s.options,
                    s.limit,
                )
                if s.kind == "csv"
                else s
            )
            for s in policy.sources
        ]
        return policy

    def allowed(self, outcome: str, tier: int, count: int, has_next: bool) -> list[str]:
        return [
            a
            for a in self.rules[outcome]
            if (a != "escalate" or self.next_tier(tier) is not None)
            and (a != "continue" or count < self.max_per_tier)
            and (a != "switch" or has_next)
        ]
