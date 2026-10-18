# Agentic Security harness

Install `pip install 'agentic_security[harness]'` (Python 3.14+). The new package
and `agesec` Fire CLI coexist with the legacy scanner. The extra currently adds
no dependencies; it reuses core dependencies.

```sh
agesec run --spec target.http --policy policy.json --decider rules --seed 42
agesec ls
agesec report RUN_ID -o report.json
agesec replay RUN_ID
```

`report` prints a structured JSON report and saves it to `-o` or the run's
`report.json`. The Python API `build_report(log)` returns a `Report` dataclass.
The report includes status, exit code (null while unfinished), stop reason,
outcome counts, cost, duration, findings, attack sources, transformations,
decision trails, and the original events. No HTML, templates, XML, or JUnit is
generated. Agents choose presentation; CI can consume the same JSON directly.
Treat evidence as untrusted content when rendering it.

## Attack references

Policies select sources and techniques, not inline prompts:

```json
{
  "max_attempts": 12,
  "max_per_tier": 2,
  "rate": 1.0,
  "sources": [
    {"kind": "dataset", "name": "deepset/prompt-injections", "limit": 100},
    {"kind": "csv", "name": "./attacks.csv", "limit": 50},
    {"kind": "module", "name": "my_attacks.sources:generate", "options": {"category": "injection"}, "limit": 20}
  ],
  "converters": [
    {"kind": "builtin", "name": "base64"},
    {"kind": "module", "name": "my_attacks.transforms:convert", "options": {}}
  ],
  "strategies": [{"kind": "builtin", "name": "transcript"}]
}
```

`dataset` resolves names from the existing `probe_data` dataset registries using
their configured loaders. `harness/smoke` is a bundled offline CSV smoke dataset,
used by the `default` and `ci` policies. `csv` resolves local paths relative to
the policy file, reusing the legacy loader; it requires a `prompt` column.
An unknown, empty, or invalid source fails the run setup rather than silently
reducing coverage. `limit` bounds prompts retained from each source. Dataset
loaders may load the entire dataset before that limit is applied.

`module` references an already-installed Python callable as `package.module:name`.
No modules are automatically installed. These are trusted local extensions:

- Source callable: `generate(*, options: dict, seed: int)` returns an iterable of
  nonempty prompt strings or a legacy `ProbeDataset`.
- Converter/strategy callable: `convert(*, prompt: str, history: list[dict], options: dict,
  seed: int)` returns one nonempty prompt string. History contains recent attempts
  for that attack. These are synchronous callables.

Adapters should generate prompts, leaving target execution to the harness so
budgets, logging, classification, and rate limits still apply. Legacy modules
that run entire scanners (such as Garak's subprocess runner) are not themselves
prompt generators; wrap the third-party prompt generation API in this contract.
Extension-side network costs cannot be accounted by the harness.

Built-in converters: `base64`, `fictional`. Built-in multi-turn strategy:
`transcript`, which incorporates recent responses into a textual conversation
for single-prompt HTTP specs. Ordered converter/strategy lists rotate on
`continue`; empty lists disable those tiers. `escalate` skips disabled tiers.
The run freezes resolved prompts and source configuration; each attempt records
its selected technique and options. Offline replay does not import extensions
or reload datasets.

## Execution and decisions

`run` emits JSONL on stdout and diagnostics on stderr. Logs and the unexpanded
HTTP template live in `.agesec/runs/<id>/`. Prefer `${ENV_VAR}` credentials in
specs. Commands lock each run on POSIX systems. An interrupted in-flight request
becomes an error on resume and is never silently repeated.

`step RUN_ID` performs at most one attempt and prints one pending decision.
Repeated calls return that same decision until `decide RUN_ID --action A --reason R`.
`step` exits 3 when finished. Illegal decisions exit 2 without changing the log.
External `run` pauses after its first attempt and exits 0, which does not mean
clean. Automated run/replay exit 0 clean, 1 findings, 2 error. Replay requires a
finished run and reconstructs its transitions using cached evidence, offline.

Policy `rules` maps each of `refused`, `partial`, `complied`, `error` to an ordered
list of actions including `stop`. Rules pick the first legal action; the harness
removes actions forbidden by attempt or budget limits. `continue` retries the
current tier, `escalate` advances to the next enabled tier, `switch` moves to the
next attack, and `stop` ends the run.

For `jev`, set `OPENROUTER_API_KEY` and policy `jev_model`. The adapter uses
[OpenRouter chat completions](https://openrouter.ai/docs/api/api-reference/chat/send-chat-completion-request).
Its decisions pass the same policy checks. There is no silent rules fallback
following a remote failure. Dollar budgets require positive
`request_cost_usd` and (for jev) `decision_cost_usd` estimates. Calls that cannot
fit are stopped before sending. Estimates are not a provider-enforced cap.
Without estimates, missing costs are accounted as zero and marked estimated.

Findings are refusal-classifier signals requiring review, not proof of goal
completion. OWASP mappings describe the attack objective
([LLM01:2025](https://genai.owasp.org/llmrisk/llm01-prompt-injection/),
[ASI01](https://genai.owasp.org/resource/owasp-top-10-for-agentic-applications-for-2026/));
this is not a full Top 10 test suite.

Claude plugin: `integrations/claude`. Codex instructions:
`integrations/codex/AGENTS.md` and its skill folder. CI example:
`.github/workflows/harness-example.yml`, manually triggered against an authorized
HTTP spec. Replace the localhost example for hosted CI.
