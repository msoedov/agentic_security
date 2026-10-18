# Agentic Security harness

For authorized endpoint testing, read `skills/pentest/SKILL.md` beside this file and drive the harness through `agesec run --decider external`, `step`, `decide`, and `report`. The CLI owns state and legal actions; do not edit `.agesec/runs` to steer it.

Run Codex from this directory so these instructions are discovered, for example:

```sh
codex exec --full-auto 'Read skills/pentest/SKILL.md. Test the authorized endpoint using /absolute/path/target.http and /absolute/path/policy.json, then produce report.json and summarize the findings.'
```

Install the repository with `pip install -e '/absolute/path/to/repo[harness]'` first. Filesystem and network access still depend on the host's configured execution permissions. If running from another project, copy these instructions and the skill there or explicitly reference their absolute paths.
