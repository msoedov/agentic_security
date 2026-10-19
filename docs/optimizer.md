# Early stop (optimizer)

When `optimize` is `true`, the scanner can stop a module before it sends all prompts. Use this option to save budget on a target that fails many prompts.

Set the option in `agentic_security.toml`:

```toml
[general]
optimize = true
```

Or use `--optimize` with the `scan` command.

## Single-shot scan

`perform_single_shot_scan` uses a scikit-optimize `Optimizer` with a Gaussian process:

```python
Optimizer([Real(0, 1)], base_estimator="GP", n_initial_points=INITIAL_OPTIMIZER_POINTS)
```

After each prompt, the scanner does these steps:

1. If there are fewer than `min_failure_samples` results, it continues to the next prompt.
2. It gives the negative failure rate to the optimizer (`ask()`, then `tell()`).
3. It reads the best failure rate from the optimizer.
4. If the best failure rate is more than `failure_rate_threshold`, it stops the module. It sends the status message "High failure rate detected".

> **NOTE:** The optimizer point does not change the prompts or the order of the prompts. The result of the optimizer is only an early stop.

## Many-shot scan

`perform_many_shot_scan` does not use the optimizer. When `optimize` is `true`, it stops the module after `min_failure_samples` results.

## Settings

Set these values in the `[fuzzer]` section of `agentic_security.toml`:

| Key | Default | Description |
| --- | --- | --- |
| `initial_optimizer_points` | `25` | The random points before the optimizer fits the model. |
| `min_failure_samples` | `5` | The minimum number of results before an early stop. |
| `failure_rate_threshold` | `0.5` | The failure rate that causes an early stop. |
