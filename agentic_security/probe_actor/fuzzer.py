import asyncio
import random
from collections.abc import AsyncGenerator

import httpx
import pandas as pd
from loguru import logger
from skopt import Optimizer
from skopt.space import Real

from agentic_security.models.schemas import Scan, ScanResult
from agentic_security.probe_actor.refusal import refusal_heuristic
from agentic_security.probe_data import msj_data
from agentic_security.probe_data.data import prepare_prompts


async def prompt_iter(prompts: list[str] | AsyncGenerator) -> AsyncGenerator[str, None]:
    if isinstance(prompts, list):
        for p in prompts:
            yield p
    else:
        async for p in prompts:
            yield p


async def perform_single_shot_scan(
    request_factory,
    max_budget: int,
    datasets: list[dict[str, str]] = [],
    tools_inbox=None,
    optimize=False,
    stop_event: asyncio.Event = None,
) -> AsyncGenerator[str, None]:
    """Perform a standard security scan."""

    try:
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

        optimizer = (
            Optimizer([Real(0, 1)], base_estimator="GP", n_initial_points=25)
            if optimize
            else None
        )
        failure_rates = []

        for module in prompt_modules:
            tokens = 0
            module_failures = 0
            module_size = 0 if module.lazy else len(module.prompts)
            logger.info(f"Scanning {module.dataset_name} {module_size}")

            async for prompt in prompt_iter(module.prompts):
                if stop_event and stop_event.is_set():
                    stop_event.clear()
                    logger.info("Scan stopped by user.")
                    yield ScanResult.status_msg("Scan stopped by user.")
                    return

                processed_prompts += 1
                progress = (
                    100 * processed_prompts / total_prompts if total_prompts else 0
                )
                prompt_tokens = len(prompt.split())
                tokens += prompt_tokens

                try:
                    r = await request_factory.fn(prompt=prompt)
                    if r.status_code >= 400:
                        raise httpx.HTTPStatusError(
                            f"HTTP {r.status_code}",
                            request=r.request,
                            response=r,
                        )

                    response_text = r.text
                    response_tokens = len(response_text.split())
                    tokens += response_tokens

                    if not refusal_heuristic(r.json()):
                        refusals.append(
                            (module.dataset_name, prompt, r.status_code, response_text)
                        )
                        module_failures += 1

                except httpx.RequestError as e:
                    logger.error(f"Request error: {e}")
                    errors.append((module.dataset_name, prompt, str(e)))
                    module_failures += 1
                    continue

                failure_rate = module_failures / max(processed_prompts, 1)
                failure_rates.append(failure_rate)
                cost = round(tokens * 1.5 / 1000_000, 2)

                yield ScanResult(
                    module=module.dataset_name,
                    tokens=round(tokens / 1000, 1),
                    cost=cost,
                    progress=round(progress, 2),
                    failureRate=round(failure_rate * 100, 2),
                ).model_dump_json()

                if optimize and len(failure_rates) >= 5:
                    next_point = optimizer.ask()
                    optimizer.tell(next_point, -failure_rate)
                    best_failure_rate = -optimizer.get_result().fun
                    if best_failure_rate > 0.5:
                        yield ScanResult.status_msg(
                            f"High failure rate detected ({best_failure_rate:.2%}). Stopping this module..."
                        )
                        break

        yield ScanResult.status_msg("Scan completed.")

        df = pd.DataFrame(
            errors + refusals, columns=["module", "prompt", "status_code", "content"]
        )
        df.to_csv("failures.csv", index=False)

    except Exception as e:
        logger.exception("Scan failed")
        yield ScanResult.status_msg(f"Scan failed: {str(e)}")
        raise e


async def perform_many_shot_scan(
    request_factory,
    max_budget: int,
    datasets: list[dict[str, str]] = [],
    probe_datasets: list[dict[str, str]] = [],
    tools_inbox=None,
    optimize=False,
    stop_event: asyncio.Event = None,
    probe_frequency: float = 0.2,
    max_ctx_length: int = 10_000,
) -> AsyncGenerator[str, None]:
    """Perform a multi-step security scan with probe injection."""
    try:
        # Load main and probe datasets
        yield ScanResult.status_msg("Loading datasets...")
        prompt_modules = prepare_prompts(
            dataset_names=[m["dataset_name"] for m in datasets if m["selected"]],
            budget=max_budget,
            tools_inbox=tools_inbox,
        )
        yield ScanResult.status_msg("Loading datasets for MSJ...")
        msj_modules = msj_data.prepare_prompts(probe_datasets)
        yield ScanResult.status_msg("Datasets loaded. Starting scan...")

        errors = []
        refusals = []
        total_prompts = sum(len(m.prompts) for m in prompt_modules if not m.lazy)
        processed_prompts = 0

        optimizer = (
            Optimizer([Real(0, 1)], base_estimator="GP", n_initial_points=25)
            if optimize
            else None
        )
        failure_rates = []

        for module in prompt_modules:
            tokens = 0
            module_failures = 0
            module_size = 0 if module.lazy else len(module.prompts)
            logger.info(f"Scanning {module.dataset_name} {module_size}")

            async for prompt in prompt_iter(module.prompts):
                if stop_event and stop_event.is_set():
                    stop_event.clear()
                    logger.info("Scan stopped by user.")
                    yield ScanResult.status_msg("Scan stopped by user.")
                    return

                processed_prompts += 1
                progress = (
                    100 * processed_prompts / total_prompts if total_prompts else 0
                )

                current_length = 0
                full_prompt = ""
                msj_module = random.choice(msj_modules)

                prompt_tokens = len(full_prompt.split())
                tokens += prompt_tokens

                injected = False
                for _ in range(20):
                    if injected:
                        break

                    m_prompt = random.choice(msj_module.prompts)
                    full_prompt += "\n" + m_prompt
                    current_length += len(m_prompt.split())
                    if current_length > max_ctx_length:
                        full_prompt = "\n" + prompt
                        injected = True
                    try:
                        # Main request
                        r = await request_factory.fn(prompt=full_prompt)
                        if r.status_code >= 400:
                            raise httpx.HTTPStatusError(
                                f"HTTP {r.status_code}",
                                request=r.request,
                                response=r,
                            )

                        response_text = r.text
                        response_tokens = len(response_text.split())
                        tokens += response_tokens

                        if injected and not refusal_heuristic(r.json()):
                            refusals.append(
                                (
                                    module.dataset_name,
                                    prompt,
                                    r.status_code,
                                    response_text,
                                )
                            )
                            module_failures += 1

                    except httpx.RequestError as e:
                        logger.error(f"Request error: {e}")
                        errors.append((module.dataset_name, prompt, str(e)))
                        module_failures += 1
                        continue

                failure_rate = module_failures / max(processed_prompts, 1)
                failure_rates.append(failure_rate)
                cost = round(tokens * 1.5 / 1000_000, 2)

                yield ScanResult(
                    module=module.dataset_name,
                    tokens=round(tokens / 1000, 1),
                    cost=cost,
                    progress=round(progress, 2),
                    failureRate=round(failure_rate * 100, 2),
                ).model_dump_json()

                if optimize and len(failure_rates) >= 5:
                    next_point = optimizer.ask()
                    optimizer.tell(next_point, -failure_rate)
                    best_failure_rate = -optimizer.get_result().fun
                    if best_failure_rate > 0.5:
                        yield ScanResult.status_msg(
                            f"High failure rate detected ({best_failure_rate:.2%}). Stopping this module..."
                        )
                        break

        yield ScanResult.status_msg("Scan completed.")

        df = pd.DataFrame(
            errors + refusals, columns=["module", "prompt", "status_code", "content"]
        )
        df.to_csv("failures.csv", index=False)

    except Exception as e:
        logger.exception("Scan failed")
        yield ScanResult.status_msg(f"Scan failed: {str(e)}")
        raise e


def scan_router(
    request_factory,
    scan_parameters: Scan,
    tools_inbox=None,
    stop_event: asyncio.Event = None,
):
    if scan_parameters.enableMultiStepAttack:
        return perform_many_shot_scan(
            request_factory=request_factory,
            max_budget=scan_parameters.maxBudget,
            datasets=scan_parameters.datasets,
            probe_datasets=scan_parameters.probe_datasets,
            tools_inbox=tools_inbox,
            optimize=scan_parameters.optimize,
            stop_event=stop_event,
        )
    else:
        return perform_single_shot_scan(
            request_factory=request_factory,
            max_budget=scan_parameters.maxBudget,
            datasets=scan_parameters.datasets,
            tools_inbox=tools_inbox,
            optimize=scan_parameters.optimize,
            stop_event=stop_event,
        )
