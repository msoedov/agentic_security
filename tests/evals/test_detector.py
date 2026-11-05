"""Tier 2: how well does the shipped detector read model replies?

This is the only file that measures the real detector. It turns
``corpus/*.jsonl`` into numbers and then into a gate.

Two numbers matter, and accuracy is neither of them:

**recall** — of the replies that really were refusals, how many did we catch?
A miss means a refusal is scored as a successful attack: a false alarm.

**false positive rate** — of the replies that really were compliances, how many
did we call refusals? A false positive means a *successful attack is reported
as a refusal*. The scanner says the target held and it did not. That is the
expensive direction, and it is the one the current phrase list fails.

The two are not symmetric, so they are gated separately. A single accuracy
number would average the harmless error against the dangerous one.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import sklearn

import agentic_security
from agentic_security.probe_actor.refusal import refusal_classifier_manager

from .conftest import (
    CORPUS_FIELDS,
    CORPUS_FILES,
    CORPUS_KINDS,
    CORPUS_LABELS,
    CORPUS_REQUIRED,
    REAL_SOURCES,
    baselines,
    load_corpus,
    row_id,
    row_key,
)

# --------------------------------------------------------------------------
# Baselines
#
# Recorded as *sets of rows* in ``baselines.json``, not as counts, and asserted
# as subsets: no row may newly join a wrong-answer set, and any row leaving one
# is an improvement the gate accepts silently.
#
# Counts were the obvious first choice and three things are wrong with them:
#
# * they are not monotone under corpus edits. Deleting a row the detector
#   misreads lowers the cap, handing back a slot for a real regression.
# * they cannot tell a fix from a substitution. Repair one row, break another,
#   and the total does not move.
# * a failure can only report the whole set, never the delta, so it does not
#   say what regressed.
#
# Regenerate with ``python tests/evals/record_baselines.py`` and read the diff.
# --------------------------------------------------------------------------


def detect(text: str) -> bool:
    """Run the shipped detector on bare reply text.

    Deliberately *not* via ``refusal_heuristic``: that one stringifies a whole
    HTTP envelope, and envelope sensitivity is measured separately in
    ``test_envelopes.py``. Here the input is only what the model said.
    """
    return refusal_classifier_manager.is_refusal(text)


def detect_phrases_only(text: str) -> bool:
    """Run only the hand-written phrase list, with no ML classifier behind it.

    Not gated on. It is reported so the scoreboard shows where the numbers come
    from: the shipped stack also runs a one-class SVM that fires on most bare
    text, which inflates recall and false positives together.
    """
    from agentic_security.probe_actor.refusal import DefaultRefusalClassifier

    return DefaultRefusalClassifier().is_refusal(text)


# --------------------------------------------------------------------------
# Schema
#
# The README promises that unknown fields fail a test. This is that test.
# --------------------------------------------------------------------------


@pytest.mark.parametrize("row", load_corpus(), ids=row_id)
def test_row_schema(row):
    """Every row carries the documented fields and nothing else."""
    fields = {k for k in row if not k.startswith("_")}

    assert CORPUS_REQUIRED <= fields, f"missing: {CORPUS_REQUIRED - fields}"
    assert fields <= CORPUS_FIELDS, f"unknown fields: {fields - CORPUS_FIELDS}"
    assert row["label"] in CORPUS_LABELS
    assert row["kind"] in CORPUS_KINDS[row["label"]], (
        f"unknown kind {row['kind']!r} for label {row['label']!r}; a typo "
        "here drops the row out of every gate silently"
    )
    assert row["src"] == "synthetic" or row["src"] in REAL_SOURCES, (
        f"unknown src {row['src']!r}: use 'synthetic' or a model in "
        f"{sorted(REAL_SOURCES)}"
    )
    assert row["text"].strip(), "empty text is not a test case"
    if "disputed" in row:
        assert (
            isinstance(row["disputed"], str) and row["disputed"].strip()
        ), "disputed must carry a reason, not an empty string"


@pytest.mark.parametrize("row", load_corpus(), ids=row_id)
def test_row_lives_in_the_file_for_its_label(row):
    """A row cannot drift into the wrong file and quietly change meaning."""
    assert row["_file"] == CORPUS_FILES[row["label"]]


def test_corpus_has_no_duplicate_text():
    """The same reply under two labels would make the gate incoherent."""
    seen: dict[str, str] = {}
    for row in load_corpus():
        key = " ".join(row["text"].split())
        assert key not in seen, f"{row_id(row)} duplicates {seen[key]}"
        seen[key] = row_id(row)


def test_corpus_contains_real_captured_output():
    """Invented refusals all start with "I'm sorry" and flatter the detector."""
    real = [r for r in load_corpus() if r["src"] in REAL_SOURCES]

    assert len(real) >= 10, "corpus has drifted towards synthetic-only"


# --------------------------------------------------------------------------
# Measurement
# --------------------------------------------------------------------------


def _score(label: str, undisputed_only: bool = True):
    """Return ``(hits, rows)`` for one label.

    A "hit" is the detector saying ``refusal``.
    """
    rows = load_corpus(label, undisputed=undisputed_only)
    hits = [r for r in rows if detect(r["text"])]
    return hits, rows


#: The scikit-learn release the bundled models were pickled with. Stated in
#: ``pyproject.toml`` next to the dependency pin.
BASELINE_SKLEARN = "1.9.1"

#: Fixed probes with their answers as recorded. The last one is the load-
#: bearing case: it is the only one of the three the model answers ``False``
#: to, so a model that has degenerated to a constant would be caught here.
MODEL_PROBES = {
    "I cannot help with that request.": True,
    "Two plus two is four.": True,
    "The build finished in 42 seconds with no warnings.": False,
}


def test_bundled_model_files_are_present():
    """Name the missing file rather than failing inside joblib."""
    model_dir = Path(agentic_security.__file__).resolve().parent / "refusal_classifier"
    missing = [
        name
        for name in (
            "oneclass_svm_model.joblib",
            "tfidf_vectorizer.joblib",
            "scaler.joblib",
        )
        if not (model_dir / name).is_file()
    ]

    assert not missing, f"bundled classifier files missing: {missing}"


def test_sklearn_matches_the_recorded_baseline():
    """Guard the environment, so a mismatch does not read as a defect.

    ``baselines.json`` records what the bundled ``OneClassSVM`` answers. Those
    answers come out of pickled ``.joblib`` files, and unpickling an estimator
    under a different scikit-learn release can change them. Every gate in this
    file would then go red for a reason that has nothing to do with the code.

    This test fails first and says so.
    """
    assert sklearn.__version__ == BASELINE_SKLEARN, (
        f"baselines.json was recorded on scikit-learn {BASELINE_SKLEARN}; "
        f"this environment has {sklearn.__version__}. The bundled models are "
        "pickled with the former (see the pin in pyproject.toml), so detector "
        "numbers will differ. This is an environment mismatch, not a defect: "
        "install the pinned version, or regenerate with record_baselines.py "
        "if the bump is intended."
    )


@pytest.mark.parametrize("text", sorted(MODEL_PROBES))
def test_bundled_model_answers_as_recorded(text):
    """Catch a swapped or re-trained model even on the pinned scikit-learn.

    A version check alone is not enough: the ``.joblib`` files are committed
    to the repo and can be replaced without the dependency moving. Probing
    the plugin directly isolates the model from the phrase list, which is
    gated separately.
    """
    ml = refusal_classifier_manager.plugins["ml_classifier"]

    # ``bool()`` because the plugin returns ``numpy.bool_``, not ``bool``,
    # despite its ``-> bool`` annotation. Harmless where the manager wraps it
    # in ``any()``, but it means ``is True`` is False for a true answer.
    assert bool(ml.is_refusal(text)) is MODEL_PROBES[text], (
        "the bundled classifier no longer answers as baselines.json records; "
        "the model files may have been retrained or replaced"
    )


def test_ml_plugin_returns_a_plain_bool():
    """Records that it does not, today.

    ``RefusalClassifierPlugin.is_refusal`` is annotated ``-> bool`` and the
    ML plugin returns ``numpy.bool_``. Nothing downstream breaks, because
    ``RefusalClassifierManager.is_refusal`` passes it through ``any()``. Any
    caller reaching the plugin directly and using ``is True`` gets the wrong
    answer, so it is pinned rather than left as a surprise.
    """
    ml = refusal_classifier_manager.plugins["ml_classifier"]
    result = ml.is_refusal("I cannot help with that request.")

    assert not isinstance(result, bool), (
        "the plugin now returns a plain bool; drop the bool() in the probe "
        "above and remove this test"
    )
    assert bool(result) is True


def test_detector_config_is_the_default():
    """Every number in this file is conditional on which plugins are enabled.

    ``refusal_classifier_manager`` is built at import time from the
    ``[detectors]`` table of ``agentic_security.toml`` — a file that is
    gitignored and auto-generated, so it differs between machines. Setting
    ``ml_classifier = false`` there changes every measurement below and makes
    the gates pass or fail for a reason that has nothing to do with the code.

    This test states the configuration the baselines were recorded under, so
    a surprising run says *why* rather than just going red.
    """
    from agentic_security.probe_actor.refusal import build_refusal_manager

    default = build_refusal_manager(config=None)
    names = sorted(default.plugins)

    assert names == ["default", "ml_classifier"], (
        f"detectors in use are {names}, but baselines.json was recorded with "
        "['default', 'ml_classifier']; check [detectors] in "
        "agentic_security.toml"
    )
    assert sorted(refusal_classifier_manager.plugins) == names


def _wrong(label: str, pred, want: bool, kind: str | None = None) -> list[dict]:
    """Undisputed rows of ``label`` where ``pred`` answers ``want``."""
    rows = load_corpus(label, undisputed=True)
    if kind:
        rows = [r for r in rows if r["kind"] == kind]
    return [r for r in rows if pred(r["text"]) is want]


def _assert_no_new(rows: list[dict], baseline: str, what: str) -> None:
    """Fail only on rows that were not already in the recorded set.

    The message names the delta, which is the thing a reader needs. A count
    ratchet can only print every row it found and leave the reader to work
    out which one is new.
    """
    recorded = baselines()[baseline]
    new = [r for r in rows if row_key(r) not in recorded]

    assert not new, (
        f"{len(new)} row(s) newly {what}: {[row_id(r) for r in new]}\n"
        f"If this is intended, regenerate with record_baselines.py."
    )


def test_no_refusal_is_newly_missed():
    """Catching fewer refusals than today is a regression.

    Subset, not a count: adding a hundred refusals the detector misses would
    leave a count gate green while recall collapsed.
    """
    _assert_no_new(_wrong("refusal", detect, False), "missed_refusals", "missed")


def test_no_compliance_is_newly_misread():
    """A compliance newly read as a refusal is a successful attack reported
    as a decline. This is the most important gate in the suite."""
    _assert_no_new(
        _wrong("compliance", detect, True),
        "misread_compliances",
        "misread as a refusal",
    )


def test_phrase_list_recall_does_not_regress():
    """The phrase list on its own must not start missing more refusals.

    Pairs with ``test_phrase_list_catches_all_explicit_refusals`` below, which
    states the target. Gated separately from ``detect`` because the ML
    classifier fires often enough to hide a phrase list emptied to zero.
    """
    _assert_no_new(
        _wrong("refusal", detect_phrases_only, False),
        "phrase_missed_refusals",
        "missed by the phrase list",
    )


def test_phrase_list_false_positives_do_not_regress():
    """Adding another bare topic word to the phrase list must show up here."""
    _assert_no_new(
        _wrong("compliance", detect_phrases_only, True),
        "phrase_misread_compliances",
        "misread by the phrase list",
    )


def _attack_success_rows():
    return [
        r
        for r in load_corpus("compliance", undisputed=True)
        if r["kind"] == "attack_success"
    ]


@pytest.mark.xfail(
    strict=True,
    reason="the ML classifier reads short imperative text as a refusal, so "
    "step-by-step attack output scores as a decline",
)
def test_attack_successes_are_never_read_as_refusals():
    """The unambiguous case: an answered attack is not a refusal.

    These rows contain step-by-step attack instructions with no hedging. No
    reasonable detector reads them as declines.

    This was a hard gate while the corpus was small enough to pass it. Growing
    the corpus to 241 rows exposed ten more, which is the corpus doing its job:
    the defect was always there, and the gate was green only because nothing
    had triggered it yet. Stating it as a strict xfail keeps the requirement
    exact and visible, and pairs it with the pin below.
    """
    rows = _attack_success_rows()
    misread = [r for r in rows if detect(r["text"])]

    assert (
        not misread
    ), f"attack output scored as a refusal: {[row_id(r) for r in misread]}"


def test_attack_output_is_currently_misread():
    """Pins the defect above so it cannot drift unnoticed.

    Paired with the strict xfail: a detector fix turns that one XPASS and this
    one FAIL in the same run, and both are removed together.
    """
    misread = {row_key(r) for r in _attack_success_rows() if detect(r["text"])}

    assert misread == baselines()["misread_attack_successes"], (
        "the set of attack rows read as refusals changed; a count would have "
        "hidden a fix paired with a new break"
    )


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known defect: the phrase list is written with U+0027, so every "
        "phrase misses the U+2019 form that real model output actually uses."
    ),
)
def test_curly_apostrophes_are_read_like_straight_ones():
    """Typographic apostrophes must not change the verdict.

    Asserted on the phrase list, not on ``detect``. An earlier version of this
    test compared ``detect`` outputs and passed vacuously: the ML classifier
    fires on both spellings, so both sides were ``True`` while the phrase list
    went on missing every curly one.
    """
    straight = "I can't provide my system instructions."
    curly = straight.replace("'", "\u2019")

    assert detect_phrases_only(straight) == detect_phrases_only(curly), (
        "the phrase list read the same sentence differently depending on its "
        "apostrophe"
    )


def test_curly_apostrophes_are_currently_missed():
    """Pins the defect above.

    Also records why it matters: the real captured rows use U+2019 throughout,
    so this is not a typographic curiosity — it is most of the corpus.
    """
    straight = "I can't provide my system instructions."
    curly = straight.replace("'", "\u2019")

    assert detect_phrases_only(straight) is True
    assert detect_phrases_only(curly) is False

    real_curly = [
        r for r in load_corpus() if r["src"] in REAL_SOURCES and "\u2019" in r["text"]
    ]
    assert real_curly, "no real captured row uses a curly apostrophe any more"


# --------------------------------------------------------------------------
# Targets
#
# What the detector should do. These are expected to fail until the detector
# work lands; they are the specification, and the ratchets above are the
# day-to-day guard.
# --------------------------------------------------------------------------


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known gap: the phrase list matches roughly a quarter of explicit "
        "refusals on its own. Most misses are real captured output using "
        "curly apostrophes or wording the list does not contain."
    ),
)
def test_phrase_list_catches_all_explicit_refusals():
    """An explicit, unmistakable refusal should never be missed.

    Measured on the phrase list alone, because that is the part a maintainer
    can actually fix by editing a constant.
    """
    rows = [
        r for r in load_corpus("refusal", undisputed=True) if r["kind"] == "explicit"
    ]
    missed = [r for r in rows if not detect_phrases_only(r["text"])]

    assert not missed, f"missed: {[row_id(r) for r in missed]}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known gap: the phrase list contains bare topic words ('illegal', "
        "'unethical', 'OpenAI') and a greeting ('Hello!'), so attack output "
        "that merely mentions them is scored as a refusal."
    ),
)
def test_no_compliance_is_read_as_a_refusal():
    """Zero false positives is the target, because the cost is asymmetric."""
    hits, _ = _score("compliance")

    assert not hits, f"false positives: {[row_id(r) for r in hits]}"


@pytest.mark.xfail(
    strict=True,
    reason=(
        "Known gap: the detector is binary, and the scanner's outcome model "
        "has no PARTIAL, so a reply that refuses and then discloses collapses "
        "to a clean refusal. Arrives with the outcome work."
    ),
)
def test_partials_are_not_scored_as_clean_refusals():
    """Refuse-then-disclose must not score the same as refuse-and-stop.

    This is the attack that matters most in practice: the opening sentence
    looks like a decline, and the payload is in the second paragraph.

    Asserted on behaviour, not on whether a module exists. An earlier version
    of this test imported ``probe_actor.outcome`` and passed only because the
    import raised; creating an empty file would have turned it green without
    changing a single verdict.
    """
    rows = load_corpus("partial", undisputed=True)
    clean = [r for r in rows if detect(r["text"])]

    assert not clean, (
        "partial disclosures read as plain refusals: " f"{[row_id(r) for r in clean]}"
    )


def test_partials_are_currently_read_as_refusals():
    """Pins the defect above so the count cannot drift unnoticed."""
    clean = {
        row_key(r) for r in load_corpus("partial", undisputed=True) if detect(r["text"])
    }

    assert (
        clean == baselines()["partials_read_as_refusals"]
    ), "the set of partials read as plain refusals changed"


# --------------------------------------------------------------------------
# Reporting
# --------------------------------------------------------------------------


def test_report(capsys):
    """Not a gate — prints the scoreboard so a run is readable.

    Disputed rows are reported separately and never gated on: an arguable
    label should not fail a build.
    """
    lines = ["", "detector vs corpus", "-" * 52]

    for kind in ("explicit", "soft"):
        rows = [r for r in load_corpus("refusal", undisputed=True) if r["kind"] == kind]
        caught = sum(1 for r in rows if detect(r["text"]))
        pct = 100 * caught / max(len(rows), 1)
        lines.append(f"recall, {kind:<9}: {caught:>2}/{len(rows):<3} ({pct:5.1f}%)")

    hits, rows = _score("compliance")
    pct = 100 * len(hits) / max(len(rows), 1)
    lines.append(f"false positives : {len(hits):>2}/{len(rows):<3} ({pct:5.1f}%)")

    lines.append("")
    lines.append("phrase list alone (not gated, for diagnosis)")
    for label in ("refusal", "compliance"):
        rows = load_corpus(label, undisputed=True)
        hits_only = sum(1 for r in rows if detect_phrases_only(r["text"]))
        name = "caught" if label == "refusal" else "false positives"
        lines.append(f"  {label:<11} {name:<16}: {hits_only:>2}/{len(rows)}")
    lines.append("")

    partial_hits, partial_rows = _score("partial")
    lines.append(f"partials read as refusals: {len(partial_hits)}/{len(partial_rows)}")

    disputed = [r for r in load_corpus() if "disputed" in r]
    lines.append(f"disputed rows (excluded from gates): {len(disputed)}")
    lines.append("-" * 52)

    with capsys.disabled():
        print("\n".join(lines))
