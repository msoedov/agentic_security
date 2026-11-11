# Blind review of the eval corpus

## What this measures

Whether the labelling rules in `RULES.md` are unambiguous enough that a second
person applies them the way the corpus does. The target is the **rules**, not
the reviewer. A disagreement is evidence a rule is underspecified.

It does **not** measure whether the corpus is "accurate" — there is no
external truth to check against. It measures reproducibility.

`answer-key.json` and `for-reviewer/` are gitignored. Generate them with
`python tests/evals/review/make_sheet.py`; only the tooling is committed.

## Send the reviewer `for-reviewer/`. Only that folder.

It holds `RULES.md` and `review-sheet.csv` and nothing else. `answer-key.json`
lives one level up on purpose — do not pass it along.

Ask them to fill `your_label` and `your_kind` for **all 30 rows**. The scorer
refuses an incomplete sheet: a blank row is not scored, so a half-finished
sheet would otherwise come back as a perfect one.

## Then

    python tests/evals/review/score.py path/to/their-filled-sheet.csv

It reports label agreement, kind agreement, both chance-corrected, a
confusion matrix, a per-stratum breakdown, and every disagreement with the
line it lives on in the corpus as it stands right now.

## Reading the result

Quote **kappa**, not raw percent: with three classes and uneven priors a
coin-flip reviewer scores about 35% for free.

| kappa | Reading |
|---|---|
| > 0.80 | The rules reproduce. No change indicated. |
| 0.60–0.80 | Usable. Look at which strata the misses sit in and sharpen those rules. |
| < 0.60 | The rules are the problem, not the reviewer. Rewrite before trusting the gate numbers. |

**Do not over-read the point estimate.** n=30 is small: one disagreement moves
kappa by roughly 0.05, so 0.78 and 0.82 are the same result. That is why a 95%
bootstrap interval is printed next to it — at 3 disagreements the interval
runs roughly [0.63, 1.00]. Read the interval and the per-stratum table
together; a kappa of 0.75 with every miss in one stratum is a very different
finding from 0.75 scattered evenly.

Even a clean 30/30 only bounds the disagreement rate at about 10%. It is
evidence the rules hold, not proof the corpus is correct.

## The sample is deliberately biased

30 rows, stratified across all ten sampleable (label, kind) pairs,
over-weighting the hard kinds. `refusal/explicit` and `refusal/soft` are 37%
of the corpus but 27% of this sheet; `roleplay` is 2% of the corpus and 7%
here. Six of the 30 are real captured replies rather than synthetic ones,
drawn in deliberately — they carry the curly apostrophes and hedging that
invented replies lack.

So the score is **not** an estimate of corpus-wide agreement. The sheet is
harder than the corpus, which makes a high score meaningful and a low score
less damning than it looks. Read the per-stratum table before concluding
anything about the whole corpus.

`comply_then_retract` is not sampled: all ten of its rows are already tagged
`disputed`, so none are eligible. If an undisputed one is ever added, give it
a `QUOTA` entry in `make_sheet.py`.

## Acting on a disagreement

Each one is one of three things:

1. **The corpus label is wrong** — fix it in `tests/evals/corpus/*.jsonl`.
2. **The rule is ambiguous** — add `"disputed": "<reason>"` to the row and
   sharpen the rule in both `RULES.md` and `tests/evals/README.md`. A disputed
   row leaves every hard gate automatically, so this is the safe move when you
   are unsure.
3. **The reviewer misread it** — leave it.

Two reviewers missing the same rule is case 2, not case 3.

Anything you change needs a re-record and a re-run:

    python tests/evals/record_baselines.py
    pytest tests/evals -m eval

Read the `baselines.json` diff before committing it.

## Reproducing the sheet

    python tests/evals/review/make_sheet.py

Fixed seed (20261106), rows sorted by content hash before sampling, so it
regenerates identically -- the package was rebuilt from scratch once and came
back byte-for-byte. The checkout is located from the script's own path, so it
works from any working directory; `--repo` and `$AGENTIC_SECURITY_REPO`
override that. Change `QUOTA` to resample.

Regenerating rewrites `answer-key.json`, which invalidates any sheet already
out with a reviewer — the scorer will catch that and refuse rather than score
the wrong pairs.

## Integrity checks the scorer runs before scoring

| Check | Why |
|---|---|
| every id present, no extras, no duplicates | a reordered or re-saved sheet |
| sha1 of each reply matches the key | the sheet was edited, or built from a different corpus |
| corpus digest matches the key | the corpus moved after the sheet went out; warns, then uses live line numbers |
| all 30 labels and kinds filled | blanks would score as free agreement |
| labels valid, kinds valid *for that label* | nonsense values would silently depress the score |
