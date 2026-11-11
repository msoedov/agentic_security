"""Tier 1: a scan that failed to run is not a passing scan.

If every request returns HTTP 500, nothing was learned about the target. That
outcome must be distinguishable from "the target refused everything", because
one is a clean bill of health and the other is a broken harness.

The practical case: a scan wired into CI, and one day the API key expires.
Every request comes back 401, not a single attack is actually tested, and the
scanner reports the same number it reports for a perfectly secure target.
"""

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
    target = targets.RaisingTarget(lambda: httpx.ConnectError("connection refused"))
    verdict = await scan(target, fuzzer_state)

    assert verdict.errors == verdict.prompts


async def test_unexpected_exception_vanishes(fuzzer_state):
    """Pins a defect: an unanticipated exception is swallowed whole.

    The catch-all in ``process_prompt`` records nothing and reports the prompt
    as not-failed, so an endpoint that raises ``ValueError`` on every request
    scans as a flawless target. The assertions are split so the failure message
    says which half is wrong.
    """
    target = targets.RaisingTarget(lambda: ValueError("exploded"))
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
    target = targets.RaisingTarget(lambda: ValueError("exploded"))
    verdict = await scan(target, fuzzer_state)

    assert verdict.errors == verdict.prompts


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: an HTTP error is scored as an attack outcome, so a "
        "target that is simply down is indistinguishable from one that "
        "refused every attack. Both score 100%, and the CLI threshold reads "
        "that as a pass."
    ),
)
async def test_dead_target_does_not_score_like_a_secure_one():
    """An unreachable target must not produce a verdict at all.

    The assertion is on ``failures``, not on ``failure_rate``, and that is
    deliberate. ``dead.failure_rate != secure.failure_rate`` would go green
    the moment the *scoring inversion* is fixed — secure would drop to 0% and
    dead would sit at 100% — while leaving this defect fully intact and the
    dead target now reported as maximally compromised. Scoring an error as an
    outcome is the defect; not resembling a secure target is a side effect.

    Ten prompts were sent and none of them were answered, so none of them
    produced anything to judge.
    """
    dead = await scan(targets.erroring_target(500), FuzzerState())

    assert dead.failures == 0, (
        f"{dead.failures}/{dead.prompts} unanswered prompts were scored as "
        "attack outcomes"
    )


async def test_dead_and_secure_targets_are_currently_identical():
    """Pins the defect above so the collision cannot change unnoticed."""
    dead = await scan(targets.erroring_target(500), FuzzerState())
    secure = await scan(targets.secure_target(), FuzzerState())

    assert dead.failures == dead.prompts
    assert dead.failure_rate == secure.failure_rate == pytest.approx(100.0)
    # The data that tells them apart is collected and then ignored: the dead
    # scan recorded ten errors and no refusals, the secure scan the reverse,
    # and the reported score consults neither.
    assert (dead.errors, dead.refusals) == (dead.prompts, 0)
    assert (secure.errors, secure.refusals) == (0, secure.prompts)


async def test_non_json_body_is_recorded_as_an_error(fuzzer_state):
    """HTTP 200 with a body that is not JSON.

    A proxy serving an HTML error page with a 200 is the common cause. The
    handler at ``process_prompt`` catches it, and this is the only test that
    reaches that branch — every other target returns a well-formed body.
    """
    verdict = await scan(targets.non_json_target(), fuzzer_state)

    assert verdict.errors == verdict.prompts
    assert verdict.refusals == 0
    assert verdict.outputs == 0


async def test_non_json_body_scores_like_a_secure_target(fuzzer_state):
    """Pins that it lands in the same collision as an HTTP error.

    Nothing was learned about this target, and it is reported at 100% the
    same way a target that refused every attack is.
    """
    verdict = await scan(targets.non_json_target(), fuzzer_state)

    assert verdict.failure_rate == pytest.approx(100.0)


async def test_error_rate_is_derivable_from_state(fuzzer_state):
    """The data needed to flag an unusable scan is already being collected.

    This is the argument for the fix being cheap: nothing new has to be
    measured, the error count just has to reach the verdict.
    """
    verdict = await scan(targets.erroring_target(503), fuzzer_state)

    assert verdict.error_rate == pytest.approx(100.0)
