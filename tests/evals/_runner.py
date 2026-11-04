"""Drives the scanner over a fake target and returns what it concluded.

Thin wrapper over ``process_prompt`` so the tests read as
"scan this target, here is the verdict" rather than as plumbing.
"""

from __future__ import annotations

from dataclasses import dataclass

from agentic_security.probe_actor.fuzzer import process_prompt

#: Stand-in attack prompts. Content is irrelevant — the fake targets do not
#: read them — but the count determines the denominator of the failure rate.
ATTACK_PROMPTS = [f"attack prompt {i}" for i in range(10)]


@dataclass
class Verdict:
    """What one scan concluded about one target."""

    prompts: int
    failures: int
    state: object

    @property
    def failure_rate(self) -> float:
        """Percent, as the UI and the CLI threshold both read it."""
        return 100.0 * self.failures / max(self.prompts, 1)

    @property
    def errors(self) -> int:
        return len(self.state.errors)

    @property
    def refusals(self) -> int:
        return len(self.state.refusals)

    @property
    def outputs(self) -> int:
        return len(self.state.outputs)

    @property
    def error_rate(self) -> float:
        return 100.0 * self.errors / max(self.prompts, 1)


async def scan(target, fuzzer_state, prompts: list[str] | None = None) -> Verdict:
    """Send every prompt to ``target`` and tally the result."""
    prompts = prompts if prompts is not None else ATTACK_PROMPTS
    failures = 0
    tokens = 0
    for prompt in prompts:
        tokens, failed = await process_prompt(
            target, prompt, tokens, "eval-module", fuzzer_state
        )
        if failed:
            failures += 1
    return Verdict(prompts=len(prompts), failures=failures, state=fuzzer_state)
