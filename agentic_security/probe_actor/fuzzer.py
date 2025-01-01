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

# TODO: full log file


async def generate_prompts(
    prompts: list[str] | AsyncGenerator,
) -> AsyncGenerator[str, None]:
    if isinstance(prompts, list):
        for prompt in prompts:
            yield prompt
    else:
        async for prompt in prompts:
            yield prompt


async def process_prompt(
    request_factory, prompt, tokens, module_name, refusals, errors
):
    try:
        response = await request_factory.fn(prompt=prompt)
        if response.status_code >= 400:
            raise httpx.HTTPStatusError(
                f"HTTP {response.status_code}",
                request=response.request,
                response=response,
            )
        response_text = response.text
        tokens += len(response_text.split())

        if refusal_heuristic(response.json()):
            refusals.append((module_name, prompt, response.status_code, response_text))
            return tokens, True
        return tokens, False

    except httpx.RequestError as exc:
        logger.error(f"Request error: {exc}")
        errors.append((module_name, prompt, "?", str(exc)))
        return tokens, True


async def perform_single_shot_scan(
    request_factory,
    max_budget: int,
    datasets: list[dict[str, str]] = [],
    tools_inbox=None,
    optimize=False,
    stop_event: asyncio.Event = None,
) -> AsyncGenerator[str, None]:
    """Perform a standard security scan."""

    selected_datasets = [m for m in datasets if m["selected"]]
    try:
        yield ScanResult.status_msg("Loading datasets...")
        prompt_modules = prepare_prompts(
            dataset_names=[m["dataset_name"] for m in selected_datasets],
            budget=max_budget,
            tools_inbox=tools_inbox,
            options=[m.get("opts", {}) for m in selected_datasets],
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

        total_tokens = 0
        tokens = 0
        should_stop = False
        for module in prompt_modules:
            if should_stop:
                break
            tokens = 0
            module_failures = 0
            module_size = 0 if module.lazy else len(module.prompts)
            logger.info(f"Scanning {module.dataset_name} {module_size}")

            async for prompt in generate_prompts(module.prompts):
                if stop_event and stop_event.is_set():
                    stop_event.clear()
                    logger.info("Scan stopped by user.")
                    yield ScanResult.status_msg("Scan stopped by user.")
                    return

                processed_prompts += 1
                progress = (
                    100 * processed_prompts / total_prompts if total_prompts else 0
                )
                total_tokens -= tokens
                tokens, failed = await process_prompt(
                    request_factory,
                    prompt,
                    tokens,
                    module.dataset_name,
                    refusals,
                    errors,
                )
                total_tokens += tokens
                # logger.debug(f"Trying prompt: {prompt}, {failed=}")
                if failed:
                    module_failures += 1
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
                        should_stop = True
                        break
                if total_tokens > max_budget:
                    logger.info("Scan ran out of budget and stopped.")
                    yield ScanResult.status_msg("Scan ran out of budget and stopped.")
                    should_stop = True
                    break

        yield ScanResult.status_msg("Scan completed.")

        failure_data = errors + refusals
        df = pd.DataFrame(
            failure_data, columns=["module", "prompt", "status_code", "content"]
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
            module_failures = 0
            module_size = 0 if module.lazy else len(module.prompts)
            logger.info(f"Scanning {module.dataset_name} {module_size}")

            async for prompt in generate_prompts(module.prompts):
                if stop_event and stop_event.is_set():
                    stop_event.clear()
                    logger.info("Scan stopped by user.")
                    yield ScanResult.status_msg("Scan stopped by user.")
                    return
                tokens = 0
                processed_prompts += 1
                progress = (
                    100 * processed_prompts / total_prompts if total_prompts else 0
                )

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
                    if tokens > max_ctx_length:
                        full_prompt = "\n" + prompt
                        injected = True

                    tokens, failed = await process_prompt(
                        request_factory,
                        full_prompt,
                        tokens,
                        module.dataset_name,
                        refusals,
                        errors,
                    )
                    if failed:
                        module_failures += 1
                        break
                    if injected:
                        break

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
