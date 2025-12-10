#!/usr/bin/env bash

set -euo pipefail

PROMPT="Ultrathink. You're a principal engineer. Do not ask me any questions. We need to improve the quality of this codebase. Implement improvements to codebase quality."
MAX_ITERS=200
MAX_EMPTY_RUNS=5
CODEX_MODEL="gpt-5.1-codex-max"

empty_runs=0

for i in $(seq 1 "$MAX_ITERS"); do
    echo "=== Codex run #$i (empty runs: $empty_runs) ==="

    # ONE-LINE EXEC CALL — bulletproof against continuation errors
    codex exec --full-auto --sandbox danger-full-access --model "$CODEX_MODEL" \
        "$PROMPT (iteration $i — focus on untouched areas, avoid reverts)"

    git add -A

    if git diff --cached --quiet; then
        echo "No changes this round."
        empty_runs=$((empty_runs + 1))

        if [ "$empty_runs" -ge "$MAX_EMPTY_RUNS" ]; then
            echo "Hit $MAX_EMPTY_RUNS empty runs. Stopping."
            break
        fi
    else
        empty_runs=0
        git commit --no-verify -m "codex quality run #$i"
    fi
done
