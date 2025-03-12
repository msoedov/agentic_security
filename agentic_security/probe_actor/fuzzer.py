import asyncio
import random
import time
from collections.abc import AsyncGenerator
from json import JSONDecodeError
from typing import Any

import httpx
from skopt import Optimizer
from skopt.space import Real

from agentic_security.http_spec import Modality
from agentic_security.logutils import logger
from agentic_security.primitives import Scan, ScanResult
from agentic_security.probe_actor.cost_module import calculate_cost
from agentic_security.probe_actor.refusal import refusal_heuristic
from agentic_security.probe_actor.state import FuzzerState
from agentic_security.probe_data import audio_generator, image_generator, msj_data
from agentic_security.probe_data.data import prepare_prompts

# Constants
MAX_PROMPT_LENGTH = 2048
BUDGET_MULTIPLIER = 100_000_000
INITIAL_OPTIMIZER_POINTS = 25
MIN_FAILURE_SAMPLES = 5
FAILURE_RATE_THRESHOLD = 0.5


async def generate_prompts(
    prompts: list[str] | AsyncGenerator,
) -> AsyncGenerator[str, None]:
    """Convert list of prompts or async generator to a unified async generator."""
    if isinstance(prompts, list):
        for prompt in prompts:
            yield prompt
    else:
        async for prompt in prompts:
            yield prompt


def get_modality_adapter(llm_spec):
    """Get the appropriate modality adapter based on the LLM spec."""
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
    request_factory,
    prompt: str,
    tokens: int,
    module_name: str,
    fuzzer_state: FuzzerState,
) -> tuple[int, bool]:
    """
    Process a single prompt and update the token count and failure status.

    Args:
        request_factory: The factory for creating requests
        prompt: The prompt to process
        tokens: Current token count
        module_name: Name of the module being processed
        fuzzer_state: State tracking object for the fuzzer

    Returns:
        Tuple of (updated token count, whether the prompt resulted in a failure)
    """
    try:
        response = await request_factory.fn(prompt=prompt)

        # Handle HTTP errors
        if response.status_code == 422:
            logger.error(f"Invalid prompt: {prompt}, error=422")
            fuzzer_state.add_error(module_name, prompt, 422, "Invalid prompt")
            return tokens, True

        if response.status_code >= 400:
            logger.error(f"HTTP {response.status_code} {response.content=}")
            fuzzer_state.add_error(
                module_name, prompt, response.status_code, response.text
            )
            return tokens, True

        # Process successful response
        response_text = response.text
        tokens += len(response_text.split())

        # Check if the response indicates a refusal
        refused = refusal_heuristic(response.json())
        if refused:
            fuzzer_state.add_refusal(
                module_name, prompt, response.status_code, response_text
            )

        fuzzer_state.add_output(module_name, prompt, response_text, refused)
        return tokens, refused

    except httpx.RequestError as exc:
        logger.error(f"Request error: {exc}")
        fuzzer_state.add_error(module_name, prompt, "?", str(exc))
        return tokens, True
    except JSONDecodeError as json_decode_error:
        logger.error(f"JSON error: {json_decode_error}")
        fuzzer_state.add_error(module_name, prompt, "?", str(json_decode_error))
        return tokens, True
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return tokens, False


async def process_prompt_batch(
    request_factory,
    prompts: list[str],
    tokens: int,
    module_name: str,
    fuzzer_state: FuzzerState,
) -> tuple[int, int]:
    """
    Process a batch of prompts in parallel.

    Args:
        request_factory: The factory for creating requests
        prompts: List of prompts to process
        tokens: Current token count
        module_name: Name of the module being processed
        fuzzer_state: State tracking object for the fuzzer

    Returns:
        Tuple of (updated token count, number of failures)
    """
    tasks = [
        process_prompt(request_factory, p, tokens, module_name, fuzzer_state)
        for p in prompts
    ]
    results = await asyncio.gather(*tasks)
    total_tokens = sum(r[0] for r in results)
    failures = sum(1 for r in results if r[1])
    return total_tokens, failures


async def scan_module(
    request_factory,
    module,
    fuzzer_state: FuzzerState,
    processed_prompts: int = 0,
    total_prompts: int = 0,
    max_budget: int = 0,
    total_tokens: int = 0,
    optimize: bool = False,
    stop_event: asyncio.Event | None = None,
) -> AsyncGenerator[dict[str, Any], None]:
    """
    Scan a single module.

    Args:
        request_factory: The factory for creating requests
        module: The prompt module to scan
        fuzzer_state: State tracking object for the fuzzer
        processed_prompts: Number of prompts processed so far
        total_prompts: Total number of prompts to process
        max_budget: Maximum token budget
        total_tokens: Current token count
        optimize: Whether to use optimization
        stop_event: Event to stop scanning

    Yields:
        ScanResult objects as the scan progresses
    """
    tokens = 0
    module_failures = 0
    module_prompts = 0
    failure_rates = []
    should_stop = False

    # Initialize optimizer if optimization is enabled
    optimizer = (
        Optimizer(
            [Real(0, 1)], base_estimator="GP", n_initial_points=INITIAL_OPTIMIZER_POINTS
        )
        if optimize
        else None
    )

    module_size = 0 if module.lazy else len(module.prompts)
    logger.info(f"Scanning {module.dataset_name} {module_size}")

    async for prompt in generate_prompts(module.prompts):
        if stop_event and stop_event.is_set():
            stop_event.clear()
            logger.info("Scan stopped by user.")
            yield ScanResult.status_msg("Scan stopped by user.")
            return

        processed_prompts += 1
        module_prompts += 1

        # Calculate progress based on total processed prompts
        progress = 100 * processed_prompts / total_prompts if total_prompts else 0
        progress = progress % 100

        total_tokens -= tokens
        start = time.time()

        tokens, failed = await process_prompt(
            request_factory,
            prompt,
            tokens,
            module.dataset_name,
            fuzzer_state=fuzzer_state,
        )

        end = time.time()
        total_tokens += tokens

        if failed:
            module_failures += 1

        failure_rate = module_failures / max(module_prompts, 1)
        failure_rates.append(failure_rate)
        cost = calculate_cost(tokens)

        response_text = fuzzer_state.get_last_output(prompt) or ""

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

        # Optimization logic
        if optimize and optimizer and len(failure_rates) >= MIN_FAILURE_SAMPLES:
            next_point = optimizer.ask()
            optimizer.tell(next_point, -failure_rate)
            best_failure_rate = -optimizer.get_result().fun
            if best_failure_rate > FAILURE_RATE_THRESHOLD:
                yield ScanResult.status_msg(
                    f"High failure rate detected ({best_failure_rate:.2%}). Stopping this module..."
                )
                should_stop = True
                break

        # Budget check
        if total_tokens > max_budget:
            logger.info(
                f"Scan ran out of budget and stopped. {total_tokens=} {max_budget=}"
            )
            yield ScanResult.status_msg(
                f"Scan ran out of budget and stopped. {total_tokens=} {max_budget=}"
            )
            should_stop = True
            break

        if should_stop:
            break

    return


async def with_error_handling(agen):
    """Wrapper to handle errors in async generators."""
    try:
        async for t in agen:
            yield t
    except Exception as e:
        logger.exception("Scan failed")
        yield ScanResult.status_msg(f"Scan failed: {str(e)}")
    finally:
        yield ScanResult.status_msg("Scan completed.")


async def perform_single_shot_scan(
    request_factory,
    max_budget: int,
    datasets: list[dict[str, str]] = [],
    tools_inbox=None,
    optimize: bool = False,
    stop_event: asyncio.Event | None = None,
    secrets: dict[str, str] = {},
) -> AsyncGenerator[str, None]:
    """
    Perform a standard security scan across all selected datasets.

    Args:
        request_factory: The factory for creating requests
        max_budget: Maximum token budget
        datasets: List of datasets to scan
        tools_inbox: Tools inbox
        optimize: Whether to use optimization
        stop_event: Event to stop scanning
        secrets: Secrets to use in the scan

    Yields:
        ScanResult objects as the scan progresses
    """
    max_budget = max_budget * BUDGET_MULTIPLIER
    selected_datasets = [m for m in datasets if m["selected"]]
    request_factory = get_modality_adapter(request_factory)

    yield ScanResult.status_msg("Loading datasets...")
    prompt_modules = prepare_prompts(
        dataset_names=[m["dataset_name"] for m in selected_datasets],
        budget=max_budget,
        tools_inbox=tools_inbox,
        options=[m.get("opts", {}) for m in selected_datasets],
    )
    yield ScanResult.status_msg("Datasets loaded. Starting scan...")

    fuzzer_state = FuzzerState()
    total_prompts = sum(len(m.prompts) for m in prompt_modules if not m.lazy)
    processed_prompts = 0

    total_tokens = 0
    for module in prompt_modules:
        module_gen = scan_module(
            request_factory=request_factory,
            module=module,
            fuzzer_state=fuzzer_state,
            processed_prompts=processed_prompts,
            total_prompts=total_prompts,
            max_budget=max_budget,
            total_tokens=total_tokens,
            optimize=optimize,
            stop_event=stop_event,
        )
        try:
            async for result in module_gen:
                yield result
        except Exception:
            logger.error("Module exception")
            continue
        # Update processed_prompts count
        module_size = 0 if module.lazy else len(module.prompts)
        processed_prompts += module_size

    yield ScanResult.status_msg("Scan completed.")
    fuzzer_state.export_failures("failures.csv")


async def perform_many_shot_scan(
    request_factory,
    max_budget: int,
    datasets: list[dict[str, str]] = [],
    probe_datasets: list[dict[str, str]] = [],
    tools_inbox=None,
    optimize: bool = False,
    stop_event: asyncio.Event | None = None,
    probe_frequency: float = 0.2,
    max_ctx_length: int = 10_000,
    secrets: dict[str, str] = {},
) -> AsyncGenerator[str, None]:
    """
    Perform a multi-step security scan with probe injection.

    Args:
        request_factory: The factory for creating requests
        max_budget: Maximum token budget
        datasets: List of datasets to scan
        probe_datasets: List of probe datasets to inject
        tools_inbox: Tools inbox
        optimize: Whether to use optimization
        stop_event: Event to stop scanning
        probe_frequency: Frequency of probe injection
        max_ctx_length: Maximum context length
        secrets: Secrets to use in the scan

    Yields:
        ScanResult objects as the scan progresses
    """
    request_factory = get_modality_adapter(request_factory)

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

    fuzzer_state = FuzzerState()
    total_prompts = sum(len(m.prompts) for m in prompt_modules if not m.lazy)
    processed_prompts = 0

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
            progress = 100 * processed_prompts / total_prompts if total_prompts else 0
            progress = progress % 100

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
                    fuzzer_state=fuzzer_state,
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

            if optimize and len(failure_rates) >= MIN_FAILURE_SAMPLES:
                yield ScanResult.status_msg(
                    f"High failure rate detected ({failure_rate:.2%}). Stopping this module..."
                )
                break

    yield ScanResult.status_msg("Scan completed.")
    fuzzer_state.export_failures("failures.csv")


def scan_router(
    request_factory,
    scan_parameters: Scan,
    tools_inbox=None,
    stop_event: asyncio.Event | None = None,
):
    """
    Route to the appropriate scan function based on scan parameters.

    Args:
        request_factory: The factory for creating requests
        scan_parameters: Scan parameters
        tools_inbox: Tools inbox
        stop_event: Event to stop scanning

    Returns:
        Async generator of scan results
    """
    if scan_parameters.enableMultiStepAttack:
        return with_error_handling(
            perform_many_shot_scan(
                request_factory=request_factory,
                max_budget=scan_parameters.maxBudget,
                datasets=scan_parameters.datasets,
                probe_datasets=scan_parameters.probe_datasets,
                tools_inbox=tools_inbox,
                optimize=scan_parameters.optimize,
                stop_event=stop_event,
                secrets=scan_parameters.secrets,
            )
        )
    else:
        return with_error_handling(
            perform_single_shot_scan(
                request_factory=request_factory,
                max_budget=scan_parameters.maxBudget,
                datasets=scan_parameters.datasets,
                tools_inbox=tools_inbox,
                optimize=scan_parameters.optimize,
                stop_event=stop_event,
                secrets=scan_parameters.secrets,
            )
        )
