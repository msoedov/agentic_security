"""Score a filled-in blind-review sheet against the answer key.

    python tests/evals/review/score.py <their-filled-sheet.csv> [--partial]

Refuses to score an incomplete or tampered sheet. Reports chance-corrected
agreement for labels *and* kinds, a bootstrap interval (n=30 is small enough
that the point estimate moves a lot), and every disagreement with the line it
lives on in the corpus as it stands right now.
"""

import argparse
import csv
import hashlib
import json
import math
import random
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
LABELS = ("refusal", "compliance", "partial")
BOOTSTRAP = 4000


def norm(s: str) -> str:
    """Lenient: casing, spacing, hyphens and stray punctuation are not errors."""
    s = (s or "").strip().lower().strip(".,;:!?'\"")
    return s.replace("-", "_").replace(" ", "_")


def kappa(pairs: list[tuple[str, str]]) -> float:
    """Cohen's kappa over (corpus, reviewer) pairs."""
    n = len(pairs)
    if not n:
        return float("nan")
    observed = sum(a == b for a, b in pairs) / n
    mine, theirs = Counter(a for a, _ in pairs), Counter(b for _, b in pairs)
    expected = sum(mine[c] / n * theirs[c] / n for c in set(mine) | set(theirs))
    if expected >= 1.0:
        return float("nan")
    return (observed - expected) / (1 - expected)


def interval(pairs: list[tuple[str, str]]) -> tuple[float, float]:
    """Percentile bootstrap. Says how much of the score is just n=30."""
    rng = random.Random(0)
    draws = []
    for _ in range(BOOTSTRAP):
        sample = [rng.choice(pairs) for _ in pairs]
        k = kappa(sample)
        if not math.isnan(k):  # a resample can come out single-class
            draws.append(k)
    if not draws:
        return (float("nan"), float("nan"))
    draws.sort()
    return (draws[int(0.025 * len(draws))], draws[int(0.975 * len(draws))])


def matrix(pairs: list[tuple[str, str]]) -> str:
    seen = [c for c in LABELS if any(c in p for p in pairs)]
    counts = Counter(pairs)
    width = max(len(c) for c in seen) + 2
    head = "".join(c[:9].rjust(10) for c in seen)
    out = [f"{'corpus \\ them':<{width}}{head}"]
    for a in seen:
        row = "".join(str(counts[(a, b)]).rjust(10) for b in seen)
        out.append(f"{a:<{width}}{row}")
    return "\n".join(out)


def live_corpus(repo: Path):
    """Re-read the corpus so disagreements point at today's line numbers."""
    sys.path.insert(0, str(repo / "tests" / "evals"))
    from conftest import CORPUS_KINDS, row_key

    by_key = {}
    rows = []
    for path in sorted((repo / "tests" / "evals" / "corpus").glob("*.jsonl")):
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("disputed"):
                continue
            k = row_key(row)
            by_key[k] = (path.name, lineno, row["label"], row["kind"])
            rows.append(f"{k}:{row['label']}:{row['kind']}")
    digest = hashlib.sha256("\n".join(sorted(rows)).encode("utf-8")).hexdigest()[:16]
    return by_key, digest, CORPUS_KINDS


def find_repo(explicit):
    import os

    cands = []
    if explicit:
        cands.append(Path(explicit))
    cands.append(HERE.parents[2])
    if os.environ.get("AGENTIC_SECURITY_REPO"):
        cands.append(Path(os.environ["AGENTIC_SECURITY_REPO"]))
    cands += [Path.cwd(), *Path.cwd().parents]
    for base in cands:
        if (base / "tests" / "evals" / "corpus").is_dir():
            return base.resolve()
    sys.exit("cannot find the repo; pass --repo or set AGENTIC_SECURITY_REPO")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sheet", help="the reviewer's filled-in CSV")
    ap.add_argument("--repo", help="path to the agentic_security checkout")
    ap.add_argument(
        "--partial",
        action="store_true",
        help="score an unfinished sheet (the result is not comparable)",
    )
    args = ap.parse_args()

    sheet = Path(args.sheet)
    if not sheet.exists():
        sys.exit(f"no such file: {sheet}")

    key_blob = json.loads((HERE / "answer-key.json").read_text(encoding="utf-8"))
    key = key_blob["rows"]
    repo = find_repo(args.repo)
    by_key, digest, CORPUS_KINDS = live_corpus(repo)

    rows = list(csv.DictReader(sheet.open(encoding="utf-8-sig")))

    # --- integrity, before any scoring -------------------------------------
    problems = []

    ids, expected_ids = [r["id"].strip() for r in rows], set(key)
    if set(ids) - expected_ids:
        problems.append(f"ids not in the key: {sorted(set(ids) - expected_ids)}")
    if expected_ids - set(ids):
        problems.append(
            f"ids missing from the sheet: {sorted(expected_ids - set(ids))}"
        )
    if len(ids) != len(set(ids)):
        dupes = [i for i, c in Counter(ids).items() if c > 1]
        problems.append(f"duplicate ids: {sorted(dupes)}")

    for r in rows:
        rid = r["id"].strip()
        if rid not in key:
            continue
        got = hashlib.sha1(r["model_reply"].encode("utf-8")).hexdigest()[:12]
        if got != key[rid]["row_key"]:
            problems.append(
                f"{rid}: the reply text does not match the key "
                "(sheet edited, or generated from a different corpus)"
            )

    if problems:
        print("sheet does not match the answer key:\n")
        for p in problems:
            print(f"  - {p}")
        sys.exit("\nnothing scored.")

    if digest != key_blob.get("corpus_digest"):
        print(
            "!! the corpus has changed since this sheet was generated.\n"
            "   The 30 replies are still the ones that were reviewed, so the\n"
            "   score is valid, but a row may have been relabelled underneath\n"
            "   it. Disagreements below are checked against the corpus as it\n"
            "   stands now.\n"
        )

    # --- completeness ------------------------------------------------------
    missing_label = [r["id"] for r in rows if not norm(r["your_label"])]
    missing_kind = [r["id"] for r in rows if not norm(r["your_kind"])]
    bad = []
    for r in rows:
        lab, knd = norm(r["your_label"]), norm(r["your_kind"])
        if lab and lab not in LABELS:
            bad.append(f"{r['id']}: label {r['your_label']!r}")
        elif lab and knd and knd not in CORPUS_KINDS[lab]:
            bad.append(f"{r['id']}: kind {r['your_kind']!r} is not valid for {lab}")

    if missing_label or missing_kind or bad:
        print("sheet is not ready to score:\n")
        if missing_label:
            print(f"  blank label ({len(missing_label)}): {missing_label}")
        if missing_kind:
            print(f"  blank kind  ({len(missing_kind)}): {missing_kind}")
        for b in bad:
            print(f"  invalid     {b}")
        if not args.partial:
            sys.exit(
                "\nA blank row is not scored, so an unfinished sheet reads as a\n"
                "perfect one. Send it back and ask for every row. Use --partial\n"
                "to score anyway, knowing the number is not comparable."
            )
        print("\n--partial: scoring the filled rows only.\n")

    scored = [r for r in rows if norm(r["your_label"]) in LABELS]
    if not scored:
        sys.exit("nothing to score.")

    # --- scoring -----------------------------------------------------------
    lab_pairs, kind_pairs, by_stratum, disagree = [], [], {}, []

    for r in scored:
        rid = r["id"].strip()
        truth = key[rid]
        theirs, mine = norm(r["your_label"]), truth["label"]
        their_kind, my_kind = norm(r["your_kind"]), truth["kind"]

        lab_pairs.append((mine, theirs))
        # Kind is scored over every row, not only rows whose label matched --
        # otherwise getting the label wrong hides the kind error too.
        kind_pairs.append((my_kind, their_kind or "<blank>"))

        slot = by_stratum.setdefault(f"{mine}/{my_kind}", {"n": 0, "lab": 0, "knd": 0})
        slot["n"] += 1
        slot["lab"] += theirs == mine
        slot["knd"] += their_kind == my_kind

        if theirs != mine or their_kind != my_kind:
            disagree.append((r, truth, theirs, their_kind))

    n = len(scored)
    lab_ok = sum(a == b for a, b in lab_pairs)
    knd_ok = sum(a == b for a, b in kind_pairs)
    lo, hi = interval(lab_pairs)

    print(f"scored        {n}/{len(rows)} rows")
    print(f"label agree   {lab_ok}/{n}  ({100*lab_ok/n:.0f}%)")
    print(f"label kappa   {kappa(lab_pairs):.2f}   95% CI [{lo:.2f}, {hi:.2f}]")
    print(f"kind  agree   {knd_ok}/{n}  ({100*knd_ok/n:.0f}%)")
    print(f"kind  kappa   {kappa(kind_pairs):.2f}   (chance-corrected, all rows)")

    print("\nlabel confusion\n" + matrix(lab_pairs))

    print("\nby stratum                          label   kind")
    for name, s in sorted(by_stratum.items()):
        flag = "  <--" if s["lab"] < s["n"] or s["knd"] < s["n"] else ""
        print(f"  {name:32} {s['lab']}/{s['n']}     {s['knd']}/{s['n']}{flag}")

    if not disagree:
        print("\nno disagreements.")
        return

    print(f"\n{len(disagree)} row(s) where the reviewer differs\n" + "=" * 70)
    for r, truth, theirs, their_kind in disagree:
        live = by_key.get(truth["row_key"])
        where = f"{live[0]}:{live[1]}" if live else f"{truth['file']}:~{truth['line']}"
        moved = ""
        if live and (live[2] != truth["label"] or live[3] != truth["kind"]):
            moved = f"  [corpus now says {live[2]}/{live[3]}]"
        kind = "label" if theirs != truth["label"] else "kind"
        print(f"\n{r['id']}  {where}  ({truth['src']})  -- {kind} differs{moved}")
        print(f"  corpus   : {truth['label']} / {truth['kind']}")
        print(f"  reviewer : {theirs} / {their_kind or '-'}")
        if r.get("notes", "").strip():
            print(f"  note     : {r['notes'].strip()}")
        text = r["model_reply"].replace("\n", " / ")
        print(f"  reply    : {text[:300]}{'...' if len(text) > 300 else ''}")

    print("\n" + "=" * 70)
    print(
        "Each row is one of three things: the corpus label is wrong (fix the\n"
        "jsonl), the rule is ambiguous (add `disputed` and sharpen RULES.md and\n"
        "tests/evals/README.md), or the reviewer misread it (leave it). Two\n"
        "reviewers missing the same rule is the second case, not the third.\n"
        "Anything you change needs:\n"
        "  python tests/evals/record_baselines.py && pytest tests/evals -m eval"
    )


if __name__ == "__main__":
    main()
