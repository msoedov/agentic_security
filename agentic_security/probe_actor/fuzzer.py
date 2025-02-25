import asyncio
import random
import time
from collections.abc import AsyncGenerator
from json import JSONDecodeError

import httpx
import pandas as pd
from loguru import logger
from skopt import Optimizer
from skopt.space import Real

from agentic_security.http_spec import Modality
from agentic_security.models.schemas import Scan, ScanResult
from agentic_security.probe_actor.cost_module import calculate_cost
from agentic_security.probe_actor.refusal import refusal_heuristic
from agentic_security.probe_data import audio_generator, image_generator, msj_data
from agentic_security.probe_data.data import prepare_prompts

# TODO: full log file

MAX_PROMPT_LENGTH = 2048


async def generate_prompts(
    prompts: list[str] | AsyncGenerator,
) -> AsyncGenerator[str, None]:
    if isinstance(prompts, list):
        for prompt in prompts:
            yield prompt
    else:
        async for prompt in prompts:
            yield prompt


def multi_modality_spec(llm_spec):
    match llm_spec.modality:
        case Modality.IMAGE:
            return image_generator.RequestAdapter(llm_spec)
        case Modality.AUDIO:
            return audio_generator.RequestAdapter(llm_spec)
        case Modality.TEXT:
            return llm_spec
        case _:
            return llm_spec


async def process_prompt(
    request_factory, prompt, tokens, module_name, refusals, errors, outputs
) -> tuple[int, bool]:
    """
    Process a single prompt and update the token count and failure status.
    """
    try:
        response = await request_factory.fn(prompt=prompt)
        if response.status_code == 422:
            logger.error(f"Invalid prompt: {prompt}, error=422")
            errors.append((module_name, prompt, 422, "Invalid prompt"))
            return tokens, True

        if response.status_code >= 400:
            logger.error(f"HTTP {response.status_code} {response.content=}")
            errors.append((module_name, prompt, response.status_code, response.text))
            return tokens, True
        response_text = response.text
        tokens += len(response_text.split())

        refused = refusal_heuristic(response.json())
        if refused:
            refusals.append((module_name, prompt, response.status_code, response_text))

        outputs.append((module_name, prompt, response_text, refused))
        return tokens, refused

    except httpx.RequestError as exc:
        logger.error(f"Request error: {exc}")
        errors.append((module_name, prompt, "?", str(exc)))
        return tokens, True
    except JSONDecodeError as json_decode_error:
        logger.error(f"Jason error: {json_decode_error}")
        errors.append((module_name, prompt, "?", str(json_decode_error)))
        return tokens, True


async def perform_single_shot_scan(
    request_factory,
    max_budget: int,
    datasets: list[dict[str, str]] = [],
    tools_inbox=None,
    optimize=False,
    stop_event: asyncio.Event = None,
    secrets: dict[str, str] = {},
) -> AsyncGenerator[str, None]:
    """Perform a standard security scan."""
    max_budget = max_budget * 100_000_000
    selected_datasets = [m for m in datasets if m["selected"]]
    request_factory = multi_modality_spec(request_factory)
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
        outputs = []
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
                start = time.time()
                tokens, failed = await process_prompt(
                    request_factory,
                    prompt,
                    tokens,
                    module.dataset_name,
                    refusals,
                    errors,
                    outputs,
                )
                end = time.time()
                total_tokens += tokens
                # logger.debug(f"Trying prompt: {prompt}, {failed=}")
                if failed:
                    module_failures += 1
                failure_rate = module_failures / max(processed_prompts, 1)
                failure_rates.append(failure_rate)
                cost = calculate_cost(tokens)

                # TODO: improve this cond
                last_output = outputs[-1] if outputs else None
                if last_output and last_output[1] == prompt:
                    response_text = last_output[2]
                else:
                    response_text = ""

                yield ScanResult(
                    module=module.dataset_name,
                    tokens=round(tokens / 1000, 1),
                    cost=cost,
                    progress=round(progress, 2),
                    failureRate=round(failure_rate * 100, 2),
                    prompt=prompt[:MAX_PROMPT_LENGTH],
                    latency=end - start,
                    model=response_text,
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
                    logger.info(
                        f"Scan ran out of budget and stopped. {total_tokens=} {max_budget=}"
                    )
                    yield ScanResult.status_msg(
                        f"Scan ran out of budget and stopped. {total_tokens=} {max_budget=}"
                    )
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
        # raise e
    finally:
        yield ScanResult.status_msg("Scan completed.")


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
    secrets: dict[str, str] = {},
) -> AsyncGenerator[str, None]:
    """Perform a multi-step security scan with probe injection."""
    request_factory = multi_modality_spec(request_factory)
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
        outputs = []
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
                        outputs,
                    )
                    if failed:
                        module_failures += 1
                        break
                    if injected:
                        break

                failure_rate = module_failures / max(processed_prompts, 1)
                failure_rates.append(failure_rate)
                cost = calculate_cost(tokens)

                yield ScanResult(
                    module=module.dataset_name,
                    tokens=round(tokens / 1000, 1),
                    cost=cost,
                    progress=round(progress, 2),
                    failureRate=round(failure_rate * 100, 2),
                    prompt=prompt[:MAX_PROMPT_LENGTH],
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
            secrets=scan_parameters.secrets,
        )
    else:
        return perform_single_shot_scan(
            request_factory=request_factory,
            max_budget=scan_parameters.maxBudget,
            datasets=scan_parameters.datasets,
            tools_inbox=tools_inbox,
            optimize=scan_parameters.optimize,
            stop_event=stop_event,
            secrets=scan_parameters.secrets,
        )
