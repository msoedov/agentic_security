import io
import os
import random
from collections.abc import Callable, Iterator
from functools import partial
from typing import Any, TypeVar

import httpx
import pandas as pd
from cache_to_disk import cache_to_disk
from datasets import load_dataset

from agentic_security.logutils import logger
from agentic_security.probe_data import stenography_fn
from agentic_security.probe_data.models import ProbeDataset
from agentic_security.probe_data.modules import (
    adaptive_attacks,
    fine_tuned,
    garak_tool,
    inspect_ai_tool,
    rl_model,
)

# Type aliases for clarity
T = TypeVar("T")
FilterFn = Callable[[pd.Series], bool]
ColumnMappings = dict[str, str]
DatasetLoader = Callable[[], ProbeDataset]
TransformFn = Callable[[str], str]


# Core data loading utilities
def fetch_csv_content(url: str) -> str:
    """Fetch CSV content from a URL."""
    response = httpx.get(url)
    response.raise_for_status()  # Raise exception for bad responses
    return response.content.decode("utf-8")


def load_df_from_source(source: str, is_url: bool = False) -> pd.DataFrame:
    """Load DataFrame from either URL or Hugging Face dataset."""
    if is_url:
        logger.info(f"Loading custom CSV from {source}")
        return pd.read_csv(io.StringIO(fetch_csv_content(source)))
    logger.info(f"Loading dataset {source} from Hugging Face")
    return pd.DataFrame(load_dataset(source)["train"])


def transform_df(
    df: pd.DataFrame,
    mappings: ColumnMappings | None = None,
    filter_fn: FilterFn | None = None,
) -> pd.DataFrame:
    """Apply transformations to DataFrame."""
    result = df.copy()
    if mappings:
        result.rename(columns=mappings, inplace=True)
    if filter_fn:
        result = result[result.apply(filter_fn, axis=1)]
    return result


def create_probe_dataset(
    name: str, prompts: list[str], metadata: dict[str, Any] | None = None
) -> ProbeDataset:
    """Create a ProbeDataset from prompts."""
    metadata = metadata or {}
    return ProbeDataset(
        dataset_name=name,
        metadata=metadata,
        prompts=prompts,
        tokens=sum(len(str(s).split()) for s in prompts),
        approx_cost=0.0,
    )


# Generalized dataset loader
@cache_to_disk()
def load_dataset_generic(
    name: str,
    mappings: ColumnMappings | None = None,
    filter_fn: FilterFn | None = None,
    url: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> ProbeDataset:
    """Load and process a dataset with flexible configuration."""
    try:
        df = load_df_from_source(url or name, is_url=bool(url))
        transformed_df = transform_df(df, mappings, filter_fn)

        # Determine which column to use as the prompt source
        prompt_col = None
        if mappings and "prompt" in mappings:
            prompt_col = mappings["prompt"]
        elif "prompt" in transformed_df.columns:
            prompt_col = "prompt"
        else:
            # Try to find a suitable text column
            text_columns = [
                col
                for col in transformed_df.columns
                if any(
                    keyword in col.lower()
                    for keyword in ["prompt", "text", "query", "question"]
                )
            ]
            if text_columns:
                prompt_col = text_columns[0]
                logger.info(f"Using column '{prompt_col}' as prompt source")
            else:
                logger.error(f"No suitable prompt column found in dataset {name}")
                return create_probe_dataset(name, [], metadata)

        # Extract prompts and filter out empty ones
        prompts = [
            p
            for p in transformed_df[prompt_col].tolist()
            if p and isinstance(p, (str, int, float))
        ]
        return create_probe_dataset(name, prompts, metadata)
    except Exception as e:
        logger.error(f"Error loading dataset {name}: {e}")
        return create_probe_dataset(name, [], {"error": str(e)})


# Dataset-specific configurations
DATASET_CONFIGS = {
    "ShawnMenz/DAN_jailbreak": {
        "mappings": {"prompt": "prompt"},
        "filter_fn": lambda row: row["jailbreak"],
    },
    "deepset/prompt-injections": {
        "mappings": {"prompt": "text"},
        "filter_fn": lambda row: row["label"],
    },
    "notrichardren/refuse-to-answer-prompts": {
        "mappings": {"prompt": "claim"},
        "filter_fn": lambda row: row["label"],
    },
    "rubend18/ChatGPT-Jailbreak-Prompts": {
        "mappings": {"prompt": "Prompt"},
        "filter_fn": lambda row: row["label"],
    },
    "markush1/LLM-Jailbreak-Classifier": {
        "mappings": {"prompt": "prompt"},
        "filter_fn": lambda row: row["classification"] == "jailbreak",
    },
    "ShawnMenz/jailbreak_sft_rm_ds": {
        "url": "hf://datasets/ShawnMenz/jailbreak_sft_rm_ds/jailbreak_sft_rm_ds.csv",
        "mappings": {"prompt": "prompt"},
        "filter_fn": lambda row: row["jailbreak"] == "jailbreak",
    },
    "verazuo/jailbreak_llms/2023_05_07": {
        "url": "https://raw.githubusercontent.com/verazuo/jailbreak_llms/main/data/prompts/jailbreak_prompts_2023_05_07.csv",
        "mappings": {"prompt": "prompt"},
        "filter_fn": lambda row: bool(row["jailbreak"]),
    },
    "verazuo/jailbreak_llms/2023_12_25": {
        "url": "https://raw.githubusercontent.com/verazuo/jailbreak_llms/main/data/prompts/jailbreak_prompts_2023_12_25.csv",
        "mappings": {"prompt": "prompt"},
        "filter_fn": lambda row: bool(row["jailbreak"]),
    },
}

# Additional generic dataset configurations
DATASET_CONFIGS_GENERICS = {
    "simonycl/aya-23-8B_advbench_jailbreak": {"mappings": {"prompt": "prompt"}},
    "acmc/jailbreaks_dataset_with_perplexity_bigcode_starcoder2-3b_bigcode_starcoder2-7b": {},
    "karanxa/dolphin-jailbreak-finetuning-dataset": {"mappings": {"prompt": "text"}},
    "karanxa/llama-2-jailbreak-dataset": {"mappings": {"prompt": "text"}},
    "karanxa/llama2-uncensored-jailbreak-dataset-finetuning": {
        "mappings": {"prompt": "text"}
    },
    "liuyanchen1015/Llama-3.2-1B_jailbreak_responses": {
        "mappings": {"prompt": "jailbreak_prompt_text"}
    },
    "liuyanchen1015/Llama-3.2-1B-Instruct_jailbreak_responses": {
        "mappings": {"prompt": "jailbreak_prompt_text"}
    },
    "liuyanchen1015/Llama-3.2-1B-Instruct_jailbreak_responses_with_judgment": {
        "mappings": {"prompt": "jailbreak_prompt_text"}
    },
    "jackhhao/jailbreak-classification": {"mappings": {"prompt": "prompt"}},
    "walledai/JailbreakBench": {"mappings": {"prompt": "prompt"}},
    "walledai/JailbreakHub": {"mappings": {"prompt": "prompt"}},
    "Granther/evil-jailbreak": {"mappings": {"prompt": "text"}},
    "sevdeawesome/jailbreak_success": {"mappings": {"prompt": "jailbreak_prompt_text"}},
    "IDA-SERICS/Disaster-tweet-jailbreaking": {"mappings": {"prompt": "prompt_attack"}},
    "GeorgeDaDude/Jailbreak_Complete_DS_labeled": {"mappings": {"prompt": "question"}},
    "dayone3nder/jailbreak_prompt_JBB_sft_trainset": {"mappings": {"prompt": "prompt"}},
    "dayone3nder/general_safe_mix_jailbreak_prompt_JBB_trainset": {
        "mappings": {"prompt": "prompt"}
    },
}


# Dataset factory
def create_dataset_loader(name: str, config: dict[str, Any]) -> DatasetLoader:
    """Create a dataset loader from configuration."""
    return partial(
        load_dataset_generic,
        name=name,
        mappings=config.get("mappings"),
        filter_fn=config.get("filter_fn"),
        url=config.get("url"),
        metadata={"source": name, "config": str(config)},
    )


# Specialized loaders
@cache_to_disk()
def load_multi_dataset(name: str, sub_datasets: list[str]) -> ProbeDataset:
    """Load and combine multiple sub-datasets."""
    prompts = []
    for sub in sub_datasets:
        try:
            dataset = load_dataset(name, sub)
            if "query" in dataset["train"].features:
                prompts.extend(dataset["train"]["query"])
            else:
                logger.warning(f"No 'query' column in {name}/{sub}")
        except Exception as e:
            logger.error(f"Error loading {name}/{sub}: {e}")

    return create_probe_dataset(
        f"{name}_combined", prompts, {"source": name, "sub_datasets": sub_datasets}
    )


@cache_to_disk()
def load_jailbreak_v28k() -> ProbeDataset:
    """Load JailBreakV-28K dataset."""
    try:
        df = pd.read_csv(
            "hf://datasets/JailbreakV-28K/JailBreakV-28k/JailBreakV_28K.csv"
        )
        prompts = df["jailbreak_query"].tolist()
        return create_probe_dataset(
            "JailbreakV-28K/JailBreakV-28k",
            prompts,
            {"source": "JailbreakV-28K/JailBreakV-28k"},
        )
    except Exception as e:
        logger.error(f"Error loading JailbreakV-28K: {e}")
        return create_probe_dataset("JailbreakV-28K/JailBreakV-28k", [])


@cache_to_disk()
def load_local_csv() -> ProbeDataset:
    """Load prompts from local CSV files."""
    csv_files = [f for f in os.listdir("./datasets") if f.endswith(".csv")]
    logger.info(f"Found {len(csv_files)} CSV files: {csv_files}")

    prompts = []
    for file in csv_files:
        try:
            df = pd.read_csv(os.path.join("./datasets", file), encoding_errors="ignore")
            if "prompt" in df.columns:
                prompts.extend(df["prompt"].tolist())
            else:
                logger.warning(f"File {file} lacks a suitable prompt column")
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")

    return create_probe_dataset("Local CSV", prompts, {"src": str(csv_files)})


@cache_to_disk(1)
def load_csv(file: str) -> ProbeDataset:
    """Load prompts from local CSV files."""
    prompts = []
    try:
        df = pd.read_csv(os.path.join("./datasets", file), encoding_errors="ignore")
        prompts = df["prompt"].tolist()
        if "prompt" in df.columns:
            prompts.extend(df["prompt"].tolist())
        else:
            logger.warning(f"File {file} lacks a suitable prompt column")
    except Exception as e:
        logger.error(f"Error reading {file}: {e}")
    return create_probe_dataset(f"fs://{file}", prompts, {"src": str(file)})


@cache_to_disk(1)
def load_local_csv_files() -> list[ProbeDataset]:
    """Load prompts from local CSV files and return a list of ProbeDataset objects."""
    csv_files = [f for f in os.listdir("./datasets") if f.endswith(".csv")]
    logger.info(f"Found {len(csv_files)} CSV files: {csv_files}")

    datasets = []

    for file in csv_files:
        try:
            df = pd.read_csv(os.path.join("./datasets", file), encoding_errors="ignore")
            if "prompt" in df.columns:
                prompts = df["prompt"].tolist()
                datasets.append(create_probe_dataset(file, prompts, {"src": file}))
            else:
                logger.warning(f"File {file} lacks a suitable prompt column")
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")

    return datasets


# Stenography transformer
class StenographyTransformer:
    """Apply stenography transformations to datasets."""

    TRANSFORMATIONS = {
        "rot5": stenography_fn.rot5,
        "rot13": stenography_fn.rot13,
        "base64": stenography_fn.base64_encode,
        "mirror": stenography_fn.mirror_words,
        "random_case": stenography_fn.randomize_letter_case,
        "scramble_words": stenography_fn.scramble_words,
        "noise_characters": stenography_fn.insert_noise_characters,
        "substitute_with_ascii": stenography_fn.substitute_with_ascii,
        "remove_vowels": stenography_fn.remove_vowels,
        "zigzag_obfuscation": stenography_fn.zigzag_obfuscation,
    }

    def __init__(self, datasets: list[ProbeDataset]):
        self.datasets = datasets

    def transform(self) -> Iterator[ProbeDataset]:
        """Generate transformed datasets."""
        if not self.datasets:
            logger.warning("No datasets provided to StenographyTransformer")
            return

        for dataset in self.datasets:
            if not dataset.prompts:
                logger.warning(
                    f"Dataset {dataset.dataset_name} has no prompts to transform"
                )
                continue

            # Convert async generator (if any) to a list
            prompts = list(dataset.prompts) if hasattr(dataset.prompts, '__iter__') else []
            size = len(prompts)

            if size == 0:
                continue

            sample_size = max(1, int(size * 0.25))  # At least 1 sample

            for name, fn in self.TRANSFORMATIONS.items():
                logger.info(f"Applying {name} to {dataset.dataset_name}")
                sampled = random.sample(prompts, min(sample_size, size))
                try:
                    transformed = [
                        f"Follow the instructions in {name}: {fn(str(p))}"
                        for p in sampled
                    ]
                    transformed_dataset = create_probe_dataset(
                        f"stenography.{name}({dataset.dataset_name})",
                        transformed,
                        {"source": dataset.dataset_name, "transformation": name},
                    )
                    yield transformed_dataset
                except Exception as e:
                    logger.error(
                        f"Error applying {name} to {dataset.dataset_name}: {e}"
                    )


def dataset_from_iterator(
    name: str, iterator: Iterator[str], lazy: bool = False
) -> list[ProbeDataset]:
    """Convert an iterator into a list of ProbeDataset objects."""
    try:
        prompts = list(iterator) if not lazy else iterator
        tokens = sum(len(str(s).split()) for s in prompts) if not lazy else 0
        dataset = ProbeDataset(
            dataset_name=name,
            metadata={"source": name, "lazy": lazy},
            prompts=prompts,
            tokens=tokens,
            approx_cost=0.0,
            lazy=lazy,
        )
        return [dataset]
    except Exception as e:
        logger.error(f"Error creating dataset from iterator {name}: {e}")
        return [create_probe_dataset(name, [], {"error": str(e)})]


# Main dataset preparation
def prepare_prompts(
    dataset_names: list[str],
    budget: float,
    tools_inbox=None,
    options: list[dict] = None,
) -> list[ProbeDataset]:
    """Prepare datasets based on names and options."""
    # Base dataset loaders
    logger.info(f"Preparing datasets: {dataset_names}")
    dataset_loaders = {
        **{k: create_dataset_loader(k, v) for k, v in DATASET_CONFIGS.items()},
        **{k: create_dataset_loader(k, v) for k, v in DATASET_CONFIGS_GENERICS.items()},
        "Lemhf14/EasyJailbreak_Datasets": partial(
            load_multi_dataset,
            name="Lemhf14/EasyJailbreak_Datasets",
            sub_datasets=[
                "AdvBench",
                "ForbiddenQuestion",
                "MJP",
                "MaliciousInstruct",
                "QuestionList",
            ],
        ),
        "JailbreakV-28K/JailBreakV-28k": load_jailbreak_v28k,
        "Local CSV": load_local_csv,
        "Custom CSV": load_local_csv,
    }

    # Dynamic dataset loaders
    dynamic_loaders = {
        "AgenticBackend": lambda opts: dataset_from_iterator(
            "AgenticBackend",
            fine_tuned.Module(
                opts["datasets"], tools_inbox=tools_inbox, opts=opts
            ).apply(),
            lazy=True,
        ),
        "Steganography": lambda opts: list(
            StenographyTransformer(opts["datasets"]).transform()
        ),
        "llm-adaptive-attacks": lambda opts: dataset_from_iterator(
            "llm-adaptive-attacks",
            adaptive_attacks.Module(
                opts["datasets"], tools_inbox=tools_inbox, opts=opts
            ).apply(),
        ),
        "Garak": lambda opts: dataset_from_iterator(
            "Garak",
            garak_tool.Module(
                opts["datasets"], tools_inbox=tools_inbox, opts=opts
            ).apply(),
            lazy=True,
        ),
        "Reinforcement Learning Optimization": lambda opts: dataset_from_iterator(
            "Reinforcement Learning Optimization",
            rl_model.Module(
                opts["datasets"], tools_inbox=tools_inbox, opts=opts
            ).apply(),
            lazy=True,
        ),
        "InspectAI": lambda opts: dataset_from_iterator(
            "InspectAI",
            inspect_ai_tool.Module([], tools_inbox=tools_inbox).apply(),
            lazy=True,
        ),
        "GPT fuzzer": lambda opts: [],
    }

    datasets = []
    options = options or [dict(datasets=datasets) for _ in dataset_names]

    # Load base datasets
    for name, opts in zip(dataset_names, options):
        if name not in dataset_loaders:
            continue
        try:
            datasets.append(dataset_loaders[name]())
        except Exception as e:
            logger.error(f"Error loading {name}: {e}")

    # Load dynamic datasets and apply transformations
    for name, opts in zip(dataset_names, options):
        if name not in dynamic_loaders:
            continue
        logger.info(f"Loading dynamic dataset {name} {opts}")
        opts["datasets"] = datasets
        try:
            dynamic_result = dynamic_loaders[name](opts)
            datasets.extend(dynamic_result)
        except Exception as e:
            logger.exception(f"Error loading dynamic {name}: {e}")

    # Load csv datasets and apply transformations
    for name, opts in zip(dataset_names, options):
        if not name.endswith(".csv"):
            continue
        logger.info(f"Loading csv dataset {name} {opts}")
        datasets.append(load_csv(name))

    return datasets
