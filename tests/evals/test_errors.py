"""Tier 1: a scan that failed to run is not a passing scan.

If every request returns HTTP 500, nothing was learned about the target. That
outcome must be distinguishable from "the target refused everything", because
one is a clean bill of health and the other is a broken harness.

The practical case: a scan wired into CI, and one day the API key expires.
Every request comes back 401, not a single attack is actually tested, and the
scanner reports the same number it reports for a perfectly secure target.
"""

from __future__ import annotations

import httpx
import pytest

from agentic_security.probe_actor.state import FuzzerState

from . import targets
from ._runner import scan

pytestmark = pytest.mark.usefixtures("pinned_detector")


@pytest.mark.parametrize("status", [400, 401, 422, 429, 500, 503])
async def test_http_errors_are_recorded_as_errors(status, fuzzer_state):
    """Errors reach the error list, whatever the status code."""
    verdict = await scan(targets.erroring_target(status), fuzzer_state)

    assert verdict.errors == verdict.prompts
    assert verdict.refusals == 0


async def test_request_errors_are_recorded(fuzzer_state):
    """A connection failure is an error, not a result."""
    target = targets.RaisingTarget(httpx.ConnectError("connection refused"))
    verdict = await scan(target, fuzzer_state)

    assert verdict.errors == verdict.prompts


async def test_unexpected_exception_vanishes(fuzzer_state):
    """Pins a defect: an unanticipated exception is swallowed whole.

    The catch-all in ``process_prompt`` records nothing and reports the prompt
    as not-failed, so an endpoint that raises ``ValueError`` on every request
    scans as a flawless target. The assertions are split so the failure message
    says which half is wrong.
    """
    target = targets.RaisingTarget(ValueError("exploded"))
    verdict = await scan(target, fuzzer_state)

    assert verdict.errors == 0, "current behaviour: unexpected errors vanish"
    assert verdict.failures == 0, "current behaviour: and the prompt counts as clean"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: the catch-all in process_prompt returns False and "
        "records nothing, so an endpoint that raises on every request scans "
        "as a flawless target."
    ),
)
async def test_unexpected_exception_should_be_recorded(fuzzer_state):
    """What should happen: the probe is recorded as an error."""
    target = targets.RaisingTarget(ValueError("exploded"))
    verdict = await scan(target, fuzzer_state)

    assert verdict.errors == verdict.prompts


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: HTTP errors are returned as refusals, so a target that "
        "is simply down is indistinguishable from one that refused every "
        "attack. Both score 100%, and the CLI threshold treats that as a pass."
    ),
)
async def test_dead_target_does_not_score_like_a_secure_one():
    """An unreachable target must not produce the same verdict as a secure one."""
    dead = await scan(targets.erroring_target(500), FuzzerState())
    secure = await scan(targets.secure_target(), FuzzerState())

    assert dead.failure_rate != secure.failure_rate


async def test_dead_and_secure_targets_are_currently_identical():
    """Pins the defect above so the collision cannot change unnoticed."""
    dead = await scan(targets.erroring_target(500), FuzzerState())
    secure = await scan(targets.secure_target(), FuzzerState())

    assert dead.failure_rate == secure.failure_rate == pytest.approx(100.0)
    # The only thing that still tells them apart is the error list, which the
    # reported score does not consult.
    assert dead.errors == 10
    assert secure.errors == 0


async def test_error_rate_is_derivable_from_state(fuzzer_state):
    """The data needed to flag an unusable scan is already being collected.

    This is the argument for the fix being cheap: nothing new has to be
    measured, the error count just has to reach the verdict.
    """
    verdict = await scan(targets.erroring_target(503), fuzzer_state)

    assert verdict.error_rate == pytest.approx(100.0)
