import os

import httpx
from loguru import logger
from pydantic import BaseModel

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
    def status_msg(cls, msg: str):
        return cls(
            module=msg,
            tokens=0,
            cost=0,
            progress=0,
            failureRate=0,
            status=True,
        ).json()


async def perform_scan(request_factory, max_budget: int, datasets: list[dict] = []):
    yield ScanResult.status_msg("Loading datasets...")
    if IS_VERCEL:
        yield ScanResult.status_msg(
            "Vercel deployment detected. Streaming messages are not supported by serverless, plz run it locally."
        )
        return
    prompt_modules = prepare_prompts(
        dataset_names=[m["dataset_name"] for m in datasets if m["selected"]],
        budget=max_budget,
    )
    yield ScanResult.status_msg("Datasets loaded. Starting scan...")

    errors = []
    refusals = []
    size = sum(len(m.prompts) for m in prompt_modules)
    step = 0
    for mi, module in enumerate(prompt_modules):
        tokens = 0
        module_failures = 0
        logger.info(f"Scanning {module.dataset_name} {len(module.prompts)}")
        for i, prompt in enumerate(module.prompts):
            step += 1
            progress = 100 * (step) / size

            # Naive token count
            tokens += len(prompt.split())
            try:
                r = await request_factory.fn(prompt=prompt)
            except httpx.RequestError as e:
                logger.error(f"Request error: {e}")
                errors.append((module.dataset_name, prompt.replace("\n", ";"), e))
                module_failures += 1
                continue
            if r.status_code >= 400:
                module_failures += 1
                errors.append(
                    (
                        module.dataset_name,
                        prompt.replace("\n", ";"),
                        r.status_code,
                        r.text,
                    )
                )
            elif not refusal_heuristic(r.json()):
                refusals.append(
                    (
                        module.dataset_name,
                        prompt.replace("\n", ";"),
                        r.status_code,
                        r.text,
                    )
                )
                module_failures += 1
            # Naive token count for llm response
            tokens += len(r.text.split())
            yield ScanResult(
                module=module.dataset_name,
                tokens=round(tokens / 1000, 1),
                cost=round(tokens * 1.5 / 1000_000, 2),
                progress=round(progress, 2),
                failureRate=100 * module_failures / max(len(module.prompts), 1),
            ).json()
    yield ScanResult.status_msg("Done.")
    import pandas as pd

    df = pd.DataFrame(
        errors + refusals, columns=["module", "prompt", "status_code", "content"]
    )
    df.to_csv("failures.csv", index=False)
    # TODO: save all results
