import asyncio
import random
import time
from collections.abc import AsyncGenerator
from json import JSONDecodeError
from typing import Any

import httpx
from skopt import Optimizer
from skopt.space import Real

from agentic_security.config import settings_var
from agentic_security.http_spec import Modality
from agentic_security.logutils import logger
from agentic_security.primitives import Scan, ScanResult
from agentic_security.probe_actor.cost_module import calculate_cost
from agentic_security.probe_actor.refusal import refusal_heuristic
from agentic_security.probe_actor.state import FuzzerState
from agentic_security.probe_data import audio_generator, image_generator, msj_data
from agentic_security.probe_data.data import prepare_prompts

MAX_PROMPT_LENGTH = settings_var("fuzzer.max_prompt_lenght")
BUDGET_MULTIPLIER = settings_var("fuzzer.budget_multiplier")
INITIAL_OPTIMIZER_POINTS = settings_var("fuzzer.initial_optimizer_points")
MIN_FAILURE_SAMPLES = settings_var("min_failure_samples")
FAILURE_RATE_THRESHOLD = settings_var("failure_rate_threshold")


async def generate_prompts(
    prompts: list[str] | AsyncGenerator,
) -> AsyncGenerator[str, None]:
    """
    Asynchronously generates and yields individual prompts.

    If the input is a list of strings, the function sequentially yields each string.
    If the input is an asynchronous generator, it forwards each generated prompt.

    Args:
        prompts (list[str] | AsyncGenerator): A list of strings or an asynchronous generator of prompts.

    Yields:
        str: An individual prompt from the list or the asynchronous generator.
    """
    if isinstance(prompts, list):
        for prompt in prompts:
            yield prompt
    else:
        async for prompt in prompts:
            yield prompt


def get_modality_adapter(llm_spec):
    """
    Returns the appropriate request adapter based on the modality of the LLM specification.

    Depending on the modality of `llm_spec`, the function selects the corresponding request adapter.
    If the modality is IMAGE or AUDIO, it returns an adapter for handling the respective type.
    If the modality is TEXT or an unrecognized type, it returns `llm_spec` as is.

    Args:
        llm_spec: An object containing modality information for the LLM.

    Returns:
        RequestAdapter | llm_spec: An instance of the appropriate request adapter
        or the original `llm_spec` if no adaptation is needed.
    """
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
    Processes a single prompt using the provided request factory and updates tracking lists.

    This function sends the given `prompt` to the `request_factory`, checks for errors, and updates
    the `tokens`, `refusals`, `errors`, and `outputs` lists accordingly. If the request fails or
    the response indicates a refusal, the function records the issue and returns the updated token count
    along with a boolean indicating whether the prompt was refused.

    Args:
        request_factory: An object with a `fn` method used to send the prompt.
        prompt (str): The input prompt to be processed.
        tokens (int): The current token count, which will be updated.
        module_name (str): The name of the module handling the request.
        fuzzer_state: State tracking object for the fuzzer

    Returns:
        tuple[int, bool]: Updated token count and a boolean indicating if the prompt was refused.
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
    Processes a batch of prompts asynchronously and aggregates the results.

    This function sends multiple prompts concurrently using `process_prompt`,
    collects the token count and failure status for each prompt, and returns
    the total number of tokens processed and the number of failed prompts.

    Args:
        request_factory: An object with a `fn` method used to send the prompts.
        prompts (list[str]): A list of input prompts to be processed.
        tokens (int): The initial token count, which will be updated.
        module_name (str): The name of the module handling the request.
        fuzzer_state: State tracking object for the fuzzer

    Returns:
        tuple[int, int]:
            - Total number of tokens processed.
            - Number of failed prompts.
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
    yield ScanResult(
        module=module.dataset_name,
        tokens=0,
        cost=0,
        progress=0,
        failureRate=0,
        prompt="",
        latency=0,
        model="",
    ).model_dump_json()

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
    """
    Wraps an asynchronous generator with error handling.

    This function iterates over an asynchronous generator, yielding its values.
    If an exception occurs, it logs the error and yields a failure message.
    Finally, it ensures that a completion message is always yielded.

    Args:
        agen: An asynchronous generator that produces scan results.

    Yields:
        ScanResult: Either a successful result, an error message if an
        exception occurs, or a completion message at the end.
    """
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
    Perform a standard security scan using a given request factory.

    This function processes security scan prompts from selected datasets while
    respecting a predefined token budget. It supports optimization, failure tracking,
    and early stopping based on budget constraints or user intervention.

    Args:
        request_factory: A factory function that generates requests for processing prompts.
        max_budget (int): The maximum token budget for the scan.
        datasets (list[dict[str, str]], optional): A list of datasets containing security prompts.
        tools_inbox: Optional additional tools for processing (default: None).
        optimize (bool, optional): Whether to enable failure rate optimization (default: False).
        stop_event (asyncio.Event, optional): An event to signal early termination (default: None).
        secrets (dict[str, str], optional): A dictionary of secrets for authentication (default: {}).

    Yields:
        str: JSON-encoded scan results or status messages.

    The function iterates over prompts, processes them asynchronously, and updates
    failure statistics and token usage. If the scan exceeds the budget or failure rate is too high,
    it stops execution. Results are saved to a CSV file upon completion.
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

    This function executes a security scan while periodically injecting probe datasets
    to test system robustness. It tracks failures, optimizes scan efficiency,
    and ensures adherence to a predefined token budget.

    Args:
        request_factory: A factory function that generates requests for processing prompts.
        max_budget (int): The maximum token budget for the scan.
        datasets (list[dict[str, str]], optional): The main datasets for scanning.
        probe_datasets (list[dict[str, str]], optional): Additional datasets for probe injection.
        tools_inbox: Optional tools for additional processing (default: None).
        optimize (bool, optional): Whether to enable failure rate optimization (default: False).
        stop_event (asyncio.Event, optional): An event to signal early termination (default: None).
        probe_frequency (float, optional): The probability of probe injection (default: 0.2).
        max_ctx_length (int, optional): The maximum context length before resetting (default: 10,000 tokens).
        secrets (dict[str, str], optional): A dictionary of secrets for authentication (default: {}).

    Yields:
        str: JSON-encoded scan results or status messages.

    This function iterates over prompts, injects probe prompts at random intervals,
    processes them asynchronously, and tracks failure rates. If failure rates exceed a threshold
    or budget is exhausted, the scan is stopped early. Results are saved to a CSV file upon completion.
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
    Route scan requests to the appropriate scanning function.

    This function determines whether to perform a multi-step or single-shot
    security scan based on the provided scan parameters.

    Args:
        request_factory: A factory function to generate requests for processing prompts.
        scan_parameters (Scan): An object containing the parameters for the scan, including:
            - enableMultiStepAttack (bool): Whether to perform a multi-step scan.
            - maxBudget (int): The maximum token budget for the scan.
            - datasets (list[dict[str, str]]): The datasets to scan.
            - probe_datasets (list[dict[str, str]], optional): Datasets for probe injection (multi-step only).
            - optimize (bool): Whether to enable optimization.
            - secrets (dict[str, str], optional): A dictionary of secrets for authentication.
        tools_inbox: Optional tools for additional processing (default: None).
        stop_event (asyncio.Event, optional): An event to signal early termination (default: None).

    Returns:
        A function wrapped with `with_error_handling`, which executes either:
        - `perform_many_shot_scan` for multi-step scanning.
        - `perform_single_shot_scan` for single-shot scanning.

    The function ensures that the appropriate scanning method is chosen based on
    the `enableMultiStepAttack` flag in `scan_parameters`.
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
