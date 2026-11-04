"""Tier 1: the real entry point, not the per-prompt helper.

Every other Tier 1 file drives ``process_prompt`` through ``_runner.scan``.
That is one prompt at a time, and it skips everything ``scan_module`` adds:
the failure-rate arithmetic, the progress accounting, and the optimizer that
can cut a module short.

Two of those matter to a verdict and are covered here.

**The arithmetic.** ``Verdict.failure_rate`` in ``_runner`` re-implements
``scan_module``. A re-implementation that nothing checks is a
second source of truth, so the first test holds them equal.

**Early stopping.** With ``optimize=True`` the module breaks out of the loop
once the running rate clears ``FAILURE_RATE_THRESHOLD``. The denominator stops
with it, so the rate that reaches the UI is measured over the prompts that ran,
not the prompts that were asked for. A target can be scored on a quarter of
its own test set without the report saying so.
"""

from __future__ import annotations

import json

import pytest

from agentic_security.probe_actor.fuzzer import scan_module
from agentic_security.probe_actor.state import FuzzerState
from agentic_security.probe_data.models import ProbeDataset

from . import targets
from ._runner import scan

pytestmark = pytest.mark.usefixtures("pinned_detector")

#: Far above anything these fakes can spend, so the budget check never fires
#: and early stopping is the only thing that can end a module early.
UNLIMITED = 10**9


def module_of(n: int) -> ProbeDataset:
    """A probe module of ``n`` prompts. Content is irrelevant to the fakes."""
    return ProbeDataset(
        dataset_name="eval-module",
        metadata={},
        prompts=[f"attack prompt {i}" for i in range(n)],
        tokens=0,
        approx_cost=0.0,
    )


async def run_module(target, n_prompts: int, optimize: bool = False) -> list[dict]:
    """Collect ``scan_module``'s progress payloads, dropping status messages."""
    results = []
    async for raw in scan_module(
        target,
        module_of(n_prompts),
        FuzzerState(),
        total_prompts=n_prompts,
        max_budget=UNLIMITED,
        optimize=optimize,
    ):
        payload = json.loads(raw)
        if not payload.get("status"):
            results.append(payload)
    # The first payload is the module header, emitted before any prompt runs.
    return results[1:]


async def test_reported_rate_matches_the_eval_runner():
    """``scan_module``'s arithmetic and ``Verdict.failure_rate`` must agree.

    This is the guard on the re-implementation. If ``fuzzer.py`` changes how
    ``failureRate`` is derived, every other Tier 1 assertion in this suite is
    measuring something the product no longer reports — and this test is the
    only thing that would say so.
    """
    for n_refused, n_complied in [(10, 0), (7, 3), (3, 7), (0, 10)]:
        target = targets.mixed_target(n_refused, n_complied)
        shipped = await run_module(target, 10)

        runner = await scan(
            targets.mixed_target(n_refused, n_complied),
            FuzzerState(),
            prompts=[f"p{i}" for i in range(10)],
        )

        assert shipped[-1]["failureRate"] == pytest.approx(
            runner.failure_rate
        ), f"scan_module and _runner disagree on {n_refused}/{n_complied}"


async def test_whole_module_runs_without_the_optimizer():
    """The baseline for the next test: every prompt is sent."""
    results = await run_module(targets.secure_target(), 20, optimize=False)

    assert len(results) == 20
    assert results[-1]["failureRate"] == pytest.approx(100.0)


async def test_optimizer_stops_the_module_early():
    """With ``optimize=True`` the module stops once the rate clears the bar.

    ``FAILURE_RATE_THRESHOLD`` is 0.5 and ``MIN_FAILURE_SAMPLES`` is 5, so a
    target that trips the detector on every prompt is cut off at the fifth.
    """
    results = await run_module(targets.secure_target(), 20, optimize=True)

    assert len(results) < 20, "optimizer did not stop the module"
    assert len(results) == 5


async def test_early_stop_truncates_the_denominator():
    """The defect: a truncated scan reports the rate of its truncated prefix.

    This target refuses the first five prompts and answers the next fifteen.
    Scored over all twenty, the current (inverted) rate is 5/20 = 25%. The
    optimizer stops at prompt five, where the running rate is 5/5, so the
    number that reaches the UI is 100%.

    Nothing in the payload records that fifteen prompts were never sent, so
    the report is not merely early — it is wrong, in the direction of alarm,
    and it would be wrong in the direction of reassurance once the scoring
    inversion is fixed.
    """
    target = targets.mixed_target(5, 15)
    truncated = await run_module(target, 20, optimize=True)

    full = await run_module(targets.mixed_target(5, 15), 20, optimize=False)

    assert truncated[-1]["failureRate"] == pytest.approx(100.0)
    assert full[-1]["failureRate"] == pytest.approx(25.0)
    assert len(truncated) == 5 and len(full) == 20


async def test_progress_does_not_reveal_the_truncation():
    """Pins that the payload gives a reader no way to spot a short module.

    ``progress`` is computed from ``total_prompts``, so the last payload of a
    truncated module reports a fraction — but a module that is merely one of
    several also reports a fraction, and the payload carries no prompt count.
    The two are indistinguishable downstream.
    """
    truncated = await run_module(targets.secure_target(), 20, optimize=True)
    last = truncated[-1]

    assert last["progress"] < 100
    assert "total_prompts" not in last
    assert "prompts_sent" not in last
