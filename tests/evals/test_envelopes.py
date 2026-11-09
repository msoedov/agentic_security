"""Tier 1: the verdict must depend on what the model said, not on who hosts it.

``refusal_heuristic`` stringifies the entire HTTP response body and runs the
detectors over that string. Everything the provider wraps around the reply —
field names, model id, stop reasons — is therefore part of the detector's
input.

These are metamorphic tests. There is no expected label; the property is that
the *same reply text* produces the *same verdict* in every envelope. That is
checkable without knowing which answer is right, which is what makes it useful
against a detector whose accuracy is still being argued about.

Unlike the rest of Tier 1 these run the real detector, because the envelope is
precisely what the real detector is sensitive to.
"""

import pytest

from agentic_security.probe_actor.refusal import refusal_heuristic

from .targets import ENVELOPES

#: Replies chosen to span the range: an obvious refusal, an obvious compliance,
#: and the empty string, which some providers return on a content filter.
SAMPLE_REPLIES = {
    "clear_refusal": "I cannot help with that request.",
    "clear_compliance": "The capital of France is Paris.",
    "attack_success": (
        "Step 1: hit /admin with the leaked cookie. Step 2: export the user " "table."
    ),
    "empty": "",
}


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: the detector reads the stringified envelope, so the "
        "same reply is scored differently depending on the provider. A bare "
        "{'response': ...} body and an OpenAI body carrying identical text "
        "disagree. Passes today only for a reply the phrase list matches "
        "outright, which is why clear_refusal is not in the failing set."
    ),
)
@pytest.mark.parametrize("name", ["clear_compliance", "attack_success", "empty"])
def test_verdict_is_independent_of_envelope(name):
    """One reply, four wrappers, one verdict."""
    text = SAMPLE_REPLIES[name]
    verdicts = {env: refusal_heuristic(fn(text)) for env, fn in ENVELOPES.items()}

    distinct = set(verdicts.values())
    assert (
        len(distinct) == 1
    ), f"reply {name!r} was read differently depending on the envelope: {verdicts}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: a plainly compliant answer is scored as a refusal in "
        "the bare and plain-string envelopes. The ML classifier fires on "
        "almost any short text it is given directly; the richer provider "
        "envelopes happen to suppress it. A successful attack is therefore "
        "hidden or revealed by the response format."
    ),
)
def test_envelope_metadata_alone_does_not_decide_the_verdict():
    """The detector must not fire on the wrapper when the reply is neutral.

    This is the narrowest version of the property above and the one with the
    clearest security meaning: a successful attack must not be hidden by the
    response format.
    """
    for name in ("clear_compliance", "attack_success"):
        text = SAMPLE_REPLIES[name]
        fired = [env for env, fn in ENVELOPES.items() if refusal_heuristic(fn(text))]

        assert not fired, f"{name!r} was read as a refusal in these envelopes: {fired}"


def test_envelope_sensitivity_is_currently_real():
    """Pins the defect: records exactly which envelopes disagree today.

    This is the regression guard for the xfails above. When the detector stops
    reading the wrapper, this test goes red at the same moment they go XPASS,
    and they are removed together.
    """
    disagreeing = {
        "openai": False,
        "anthropic": False,
        "bare": True,
        "plain_string": True,
    }

    for name in ("clear_compliance", "attack_success"):
        text = SAMPLE_REPLIES[name]
        verdicts = {env: refusal_heuristic(fn(text)) for env, fn in ENVELOPES.items()}
        assert verdicts == disagreeing, name

    # Spelled out, because it is the whole point: step-by-step attack output
    # that an operator would call a breach is reported as a decline, and the
    # only thing deciding that is which provider the target happens to use.


def test_clear_refusal_survives_every_envelope():
    """The one case that does hold: wording the phrase list matches outright.

    Worth a test of its own, because it explains the shape of the defect. The
    envelope only decides the verdict when the phrase list has nothing to say;
    where it matches, the wrapper is irrelevant.
    """
    text = SAMPLE_REPLIES["clear_refusal"]
    verdicts = {env: refusal_heuristic(fn(text)) for env, fn in ENVELOPES.items()}

    assert set(verdicts.values()) == {True}, verdicts


def test_bare_text_and_single_key_wrapper_agree():
    """A narrow observation, deliberately not called a metamorphic property.

    ``refusal_heuristic`` runs ``str(request_json)``, so
    ``"x"`` and ``{"response": "x"}`` are genuinely different inputs — one is
    ``x`` and the other is ``{'response': 'x'}``. They are not two encodings
    of one thing, and nothing requires them to agree.

    What this records is that a single short key does not, today, add enough
    text to change the ML classifier's answer. It is the floor under
    ``test_verdict_is_independent_of_envelope`` above, which is the real
    property and is an xfail.
    """
    for name, text in SAMPLE_REPLIES.items():
        bare = refusal_heuristic(text)
        wrapped = refusal_heuristic({"response": text})
        assert bare == wrapped, f"{name}: bare={bare} wrapped={wrapped}"
