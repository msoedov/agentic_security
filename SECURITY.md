# Security policy

## Reporting a vulnerability

Please don't open a public issue for a security problem. Report it privately
through GitHub: on this repository, open **Security → Report a
vulnerability**. Only the maintainers can see the report.

Include what you found, how to reproduce it, and what an attacker could do
with it. Use fake keys and placeholder endpoints in the report, as described in
[CONTRIBUTING.md](CONTRIBUTING.md).

We'll acknowledge the report within a few days, keep you updated while we
work on a fix, and credit you in the release notes unless you'd rather we
didn't.

## Supported versions

Security fixes go into the latest release and `main`. Please check that the
problem still happens on `main` before reporting.

## What's in scope

Agentic Security runs on your machine or in your CI with your own
credentials. The boundaries that matter most:

- **The judge.** The LLM refusal classifier reads output from the model under
  test, which an attacker controls. Output that changes a verdict, for example
  by escaping the `<target_output>` fence in
  `agentic_security/refusal_classifier/untrusted.py`, is in scope.
- **The local server.** The FastAPI app (`agentic_security` with no
  arguments) and its CORS settings. A web page that can drive a scan or read
  results from another origin is in scope.
- **Credential handling.** Keys from HTTP specs, `agentic_security.toml` or
  the environment that show up in logs, reports, harness run logs or
  requests to hosts other than the target.
- **The `agesec` harness.** Decisions or run logs that can be forged or
  replayed to report a finding that didn't happen, or hide one that did.

Out of scope:

- Problems that need code already running as your own user account, which
  can read your keys and config directly.
- The scanner sending attack prompts to a target you configured. That is its
  job. Point it only at systems you are allowed to test.
- Jailbreaks of third-party models found *with* the scanner. Report those to
  the model's vendor.
