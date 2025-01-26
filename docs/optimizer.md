# Bayesian Optimization in Security Fuzzing

The fuzzer implements an optimization system using scikit-optimize (skopt) to minimize failure rates during security scans. This document explains the optimizer's implementation and behavior.

## Overview

The optimizer is used in both single-shot and many-shot scanning modes when the `optimize` parameter is True. It dynamically adjusts scan parameters to minimize failure rates while staying within budget constraints.

## Implementation Details

### Initialization

The optimizer is initialized with:

```python
Optimizer(
    [Real(0, 1)],  # Single parameter space (0 to 1)
    base_estimator="GP",  # Gaussian Process estimator
    n_initial_points=25  # Initial exploration points
)
```

### Optimization Process

1. **Parameter Space**: A single real-valued parameter between 0 and 1
1. **Objective**: Minimize the failure rate (negative failure rate is maximized)
1. **Update Mechanism**:
   ```python
   next_point = optimizer.ask()
   optimizer.tell(next_point, -failure_rate)
   ```
1. **Early Stopping**: If best failure rate exceeds 50%:
   ```python
   if best_failure_rate > 0.5:
       yield ScanResult.status_msg(
           f"High failure rate detected ({best_failure_rate:.2%}). Stopping this module..."
       )
       break
   ```

## Usage in Scanning

The optimizer is integrated into both scan types:

### Single-shot Scan

- Used in `perform_single_shot_scan()`
- Optimizes failure rates across prompt modules
- Considers token budget constraints

### Many-shot Scan

- Used in `perform_many_shot_scan()`
- Handles more complex multi-step attacks
- Maintains separate failure rate tracking

## Key Parameters

| Parameter | Description |
|-----------|-------------|
| base_estimator | Gaussian Process (GP) used for optimization |
| n_initial_points | 25 initial exploration points |
| Real(0, 1) | Single parameter space being optimized |
| failure_rate | Current failure rate being minimized |

## Optimization Flow

1. Initialize optimizer with GP estimator
1. Collect initial 25 data points
1. For each prompt:
   - Calculate current failure rate
   - Update optimizer with new point
   - Check for early stopping conditions
1. Continue until scan completes or budget exhausted

## Error Handling

The optimizer is wrapped in try/except blocks to ensure scan failures don't crash the entire process. Any optimization errors are logged and the scan continues with default parameters.
