"""Tier 1: does the score match reality?

Ground truth is fixed by construction. A target that refuses every attack is
secure; a target that carries out every attack is compromised. The only thing
under test is whether the number the scanner reports points the same way.

These tests pin the detector (see ``conftest.PinnedDetector``). A failure here
means the scoring pipeline changed, not that the detector did.
"""

import pytest

from agentic_security.probe_actor.state import FuzzerState

from . import targets
from ._runner import scan

pytestmark = pytest.mark.usefixtures("pinned_detector")


async def test_secure_target_is_recognised_as_refusing(fuzzer_state):
    """Sanity check: the pinned detector sees the secure target's refusals.

    If this fails, every other result in the file is meaningless.
    """
    verdict = await scan(targets.secure_target(), fuzzer_state)

    assert verdict.refusals == verdict.prompts
    assert verdict.errors == 0


async def test_broken_target_is_recognised_as_complying(fuzzer_state):
    """Mirror of the above for the compromised target.

    ``outputs == prompts`` is the part that carries weight. Without it a 200
    with an empty body satisfies the other two assertions, so a regression
    that dropped every reply on the floor would look like a clean pass.
    """
    verdict = await scan(targets.broken_target(), fuzzer_state)

    assert verdict.refusals == 0
    assert verdict.errors == 0
    assert verdict.outputs == verdict.prompts


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: refusals are counted as failures, so the score is "
        "inverted. A target that refuses every attack scores 100% failure. "
        "Remove this xfail when the outcome model lands."
    ),
)
async def test_secure_target_scores_low(fuzzer_state):
    """A target that refuses everything should score near zero failure."""
    verdict = await scan(targets.secure_target(), fuzzer_state)

    assert verdict.failure_rate == pytest.approx(0.0)


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: compliance is not counted as a failure, so a fully "
        "compromised target scores a clean 0%. Remove with the outcome model."
    ),
)
async def test_broken_target_scores_high(fuzzer_state):
    """A target that carries out every attack should score near 100% failure."""
    verdict = await scan(targets.broken_target(), fuzzer_state)

    assert verdict.failure_rate == pytest.approx(100.0)


@pytest.mark.xfail(
    strict=True,
    reason="Known defect: score inversion (see test_secure_target_scores_low).",
)
async def test_secure_target_scores_better_than_broken_one():
    """The weakest possible claim, and still false today.

    Never mind calibration — the secure target should simply not score *worse*
    than the compromised one. This is the test to watch: it holds under any
    sane scoring scheme, so if it is red the ordering itself is wrong.
    """
    secure = await scan(targets.secure_target(), FuzzerState())
    broken = await scan(targets.broken_target(), FuzzerState())

    assert secure.failure_rate < broken.failure_rate


async def test_scoring_is_currently_inverted():
    """Pins the defect so it cannot change unnoticed.

    This test asserts the *wrong* behaviour on purpose. It is the regression
    guard for the xfails above: when the fix lands, this one goes red at the
    same moment they go XPASS, and both are removed together.
    """
    secure = await scan(targets.secure_target(), FuzzerState())
    broken = await scan(targets.broken_target(), FuzzerState())

    assert secure.failure_rate == pytest.approx(100.0), "secure target"
    assert broken.failure_rate == pytest.approx(0.0), "compromised target"


@pytest.mark.parametrize(
    ("n_refused", "n_complied"),
    [(10, 0), (7, 3), (5, 5), (3, 7), (0, 10)],
)
async def test_failure_rate_tracks_refusals_not_compliance(
    n_refused, n_complied, fuzzer_state
):
    """Shows the exact shape of the defect across the whole range.

    Under correct scoring the number would climb with ``n_complied``. It climbs
    with ``n_refused`` instead, in a straight line, which is what makes the
    inversion a one-line bug rather than a calibration problem.

    ``(5, 5)`` is the one case that pins nothing: an inverted line and a
    correct one cross at the midpoint, so both answer 50.0. It stays in the
    sweep because the *shape* is the point, but it is not evidence on its own.
    Every other parameter here separates the two.
    """
    target = targets.mixed_target(n_refused, n_complied)
    verdict = await scan(target, fuzzer_state, prompts=[f"p{i}" for i in range(10)])

    assert verdict.failure_rate == pytest.approx(n_refused * 10.0)
