import os
from typing import AsyncGenerator

import httpx
import numpy as np
import pandas as pd
from loguru import logger
from pydantic import BaseModel
from skopt import Optimizer
from skopt.space import Real

from agentic_security.probe_actor.refusal import refusal_heuristic
from agentic_security.probe_data.data import prepare_prompts

IS_VERCEL = os.getenv("IS_VERCEL", "f") == "t"


class ScanResult(BaseModel):
    module: str
    tokens: float
    cost: float
    progress: float
    failureRate: float = 0.0
    status: bool = False

    @classmethod
    def status_msg(cls, msg: str) -> str:
        return cls(
            module=msg,
            tokens=0,
            cost=0,
            progress=0,
            failureRate=0,
            status=True,
        ).model_dump_json()


async def prompt_iter(prompts: list[str] | AsyncGenerator) -> AsyncGenerator[str, None]:
    if isinstance(prompts, list):
        for p in prompts:
            yield p
    else:
        async for p in prompts:
            yield p


async def perform_scan(
    request_factory,
    max_budget: int,
    datasets: list[dict[str, str]] = [],
    tools_inbox=None,
    optimize=False,
) -> AsyncGenerator[str, None]:
    if IS_VERCEL:
        yield ScanResult.status_msg(
            "Vercel deployment detected. Streaming messages are not supported by serverless, please run it locally."
        )
        return

    yield ScanResult.status_msg("Loading datasets...")
    prompt_modules = prepare_prompts(
        dataset_names=[m["dataset_name"] for m in datasets if m["selected"]],
        budget=max_budget,
        tools_inbox=tools_inbox,
    )
    yield ScanResult.status_msg("Datasets loaded. Starting scan...")

    errors = []
    refusals = []
    total_prompts = sum(len(m.prompts) for m in prompt_modules if not m.lazy)
    processed_prompts = 0

    failure_rates = []

    for module in prompt_modules:
        tokens = 0
        module_failures = 0
        module_size = 0 if module.lazy else len(module.prompts)
        logger.info(f"Scanning {module.dataset_name} {module_size}")
        optimizer = Optimizer(
            [Real(0, 1)], base_estimator="GP", n_initial_points=25, acq_func="EI"
        )
        should_stop_early = False
        async for prompt in prompt_iter(module.prompts):
            processed_prompts += 1
            progress = 100 * processed_prompts / total_prompts if total_prompts else 0

            tokens += len(prompt.split())
            try:
                r = await request_factory.fn(prompt=prompt)
                if r.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"HTTP {r.status_code}", request=r.request, response=r
                    )

                response_text = r.text
                tokens += len(response_text.split())

                if not refusal_heuristic(r.json()):
                    refusals.append(
                        (module.dataset_name, prompt, r.status_code, response_text)
                    )
                    module_failures += 1
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                logger.error(f"Request error: {e}")
                errors.append((module.dataset_name, prompt, str(e)))
                module_failures += 1
                continue

            failure_rate = module_failures / max(processed_prompts, 1)
            failure_rates.append(failure_rate)

            yield ScanResult(
                module=module.dataset_name,
                tokens=round(tokens / 1000, 1),
                cost=round(tokens * 1.5 / 1000_000, 2),
                progress=round(progress, 2),
                failureRate=round(failure_rate * 100, 2),
            ).model_dump_json()

            if not optimize:
                continue
            # Use the optimizer to decide whether to stop early
            if len(failure_rates) >= 5:  # Wait for at least 5 data points
                next_point = optimizer.ask()
                optimizer.tell(
                    next_point, -failure_rate
                )  # We want to minimize failure rate

                # Get the best point found so far
                best_failure_rate = -optimizer.get_result().fun

                # If the best failure rate is high, consider stopping
                if best_failure_rate > 0.5:  # Threshold can be adjusted
                    yield ScanResult.status_msg(
                        f"High failure rate detected ({best_failure_rate:.2%}). Stopping this module..."
                    )
                    should_stop_early = True
                    break  # Break out of the prompt loop

        if should_stop_early:
            continue  # Move to the next module

    yield ScanResult.status_msg("Scan completed.")

    df = pd.DataFrame(
        errors + refusals, columns=["module", "prompt", "status_code", "content"]
    )
    df.to_csv("failures.csv", index=False)
