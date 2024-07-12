import io
import os
import random
from dataclasses import dataclass
from functools import lru_cache

import httpx
import pandas as pd
from loguru import logger

from agentic_security.probe_data import stenography_fn
from agentic_security.probe_data.modules import (
    adaptive_attacks,
    garak_tool,
    inspect_ai_tool,
)

IS_VERCEL = os.getenv("IS_VERCEL", "f") == "t"

if not IS_VERCEL:
    from cache_to_disk import cache_to_disk
else:
    # Read only fs in vercel, just mock no-op decorator
    def cache_to_disk(*_):
        def decorator(fn):
            def wrapper(*args, **kwargs):
                return fn(*args, **kwargs)

            return wrapper

        return decorator


@dataclass
class ProbeDataset:
    dataset_name: str
    metadata: dict
    prompts: list[str]
    tokens: int
    approx_cost: float
    lazy: bool = False

    def metadata_summary(self):
        return {
            "dataset_name": self.dataset_name,
            "num_prompts": len(self.prompts),
            "tokens": self.tokens,
            "approx_cost": self.approx_cost,
        }


def count_words_in_list(str_list):
    """Calculate the total number of words in a given list of strings.

    :param str_list: List of strings
    :return: Total number of words across all strings in the list
    """
    total_words = sum(len(s.split()) for s in str_list)
    return total_words


@cache_to_disk()
def load_dataset_v1():
    from datasets import load_dataset

    dataset = load_dataset("ShawnMenz/DAN_jailbreak")
    dp = dataset["train"]["prompt"]
    dj = dataset["train"]["jailbreak"]
    # good_prompts = [p for p, j in zip(dp, dj) if not j]
    bad_prompts = [p for p, j in zip(dp, dj) if j]

    return ProbeDataset(
        dataset_name="ShawnMenz/DAN_jailbreak",
        metadata={},
        prompts=bad_prompts,
        tokens=count_words_in_list(bad_prompts),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_dataset_v2():
    from datasets import load_dataset

    dataset = load_dataset("deepset/prompt-injections")
    dp = dataset["train"]["text"]
    dj = dataset["train"]["label"]
    # good_prompts = [p for p, j in zip(dp, dj) if not j]
    bad_prompts = [p for p, j in zip(dp, dj) if j]

    return ProbeDataset(
        dataset_name="deepset/prompt-injections",
        metadata={},
        prompts=bad_prompts,
        tokens=count_words_in_list(bad_prompts),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_dataset_v4():
    from datasets import load_dataset

    dataset = dataset = load_dataset("notrichardren/refuse-to-answer-prompts")
    dp = dataset["train"]["claim"]
    dj = dataset["train"]["label"]
    # good_prompts = [p for p, j in zip(dp, dj) if not j]
    bad_prompts = [p for p, j in zip(dp, dj) if j]

    return ProbeDataset(
        dataset_name="notrichardren/refuse-to-answer-prompts",
        metadata={},
        prompts=bad_prompts,
        tokens=count_words_in_list(bad_prompts),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_dataset_v3():
    from datasets import load_dataset

    dataset = load_dataset("rubend18/ChatGPT-Jailbreak-Prompts")
    bad_prompts = dataset["train"]["Prompt"]
    return ProbeDataset(
        dataset_name="rubend18/ChatGPT-Jailbreak-Prompts",
        metadata={},
        prompts=bad_prompts,
        tokens=count_words_in_list(bad_prompts),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_dataset_v6():
    from datasets import load_dataset

    dataset = load_dataset("markush1/LLM-Jailbreak-Classifier")
    bad_prompts = [
        p
        for p, c in zip(dataset["train"]["prompt"], dataset["train"]["classification"])
        if c == "jailbreak"
    ]
    return ProbeDataset(
        dataset_name="markush1/LLM-Jailbreak-Classifier",
        metadata={},
        prompts=bad_prompts,
        tokens=count_words_in_list(bad_prompts),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_dataset_v7():

    splits = {
        "mini_JailBreakV_28K": "JailBreakV_28K/mini_JailBreakV_28K.csv",
        "JailBreakV_28K": "JailBreakV_28K/JailBreakV_28K.csv",
    }
    df = pd.read_csv(
        "hf://datasets/JailbreakV-28K/JailBreakV-28k/" + splits["JailBreakV_28K"]
    )
    bad_prompts = df["jailbreak_query"].tolist()
    print(df.shape)
    return ProbeDataset(
        dataset_name="JailbreakV-28K/JailBreakV-28k",
        metadata={},
        prompts=bad_prompts,
        tokens=count_words_in_list(bad_prompts),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_dataset_v8():

    df = pd.read_csv(
        "hf://datasets/ShawnMenz/jailbreak_sft_rm_ds/jailbreak_sft_rm_ds.csv",
        names=["jailbreak", "prompt"],
    )
    filtered = df[df["jailbreak"] == "jailbreak"]["prompt"].tolist()
    return ProbeDataset(
        dataset_name="JailbreakV-28K/JailBreakV-28k",
        metadata={},
        prompts=filtered,
        tokens=count_words_in_list(filtered),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_dataset_v5():
    from datasets import load_dataset

    ds = []
    for c in [
        "AdvBench",
        "ForbiddenQuestion",
        "MJP",
        "MaliciousInstruct",
        "QuestionList",
    ]:
        dataset = load_dataset("Lemhf14/EasyJailbreak_Datasets", c)
        bad_prompts = dataset["train"]["query"]
        ds.extend(bad_prompts)

    return ProbeDataset(
        dataset_name="Lemhf14/EasyJailbreak_Datasets",
        metadata={},
        prompts=ds,
        tokens=count_words_in_list(ds),
        approx_cost=0.0,
    )


@cache_to_disk()
def load_generic_csv(url, name, column="prompt", predicator=None):
    r = httpx.get(url)
    content = r.content
    df = pd.read_csv(io.StringIO(content.decode("utf-8")))
    logger.info(f"Loaded {len(df)} prompts from {url}")
    filtered_prompts = df[df.apply(predicator, axis=1)][column].tolist()
    return ProbeDataset(
        dataset_name=name,
        metadata={},
        prompts=filtered_prompts,
        tokens=count_words_in_list(filtered_prompts),
        approx_cost=0.0,
    )


def prepare_prompts(dataset_names, budget, tools_inbox=None):
    # ## Datasets used and cleaned:
    # markush1/LLM-Jailbreak-Classifier
    # 1. Open-Orca/OpenOrca
    # 2. ShawnMenz/DAN_jailbreak
    # 3. EddyLuo/JailBreakV_28K
    # 4. https://raw.githubusercontent.com/verazuo/jailbreak_llms/main/data/jailbreak_prompts.csv

    dataset_map = {
        "ShawnMenz/DAN_jailbreak": load_dataset_v1,
        "deepset/prompt-injections": load_dataset_v2,
        "notrichardren/refuse-to-answer-prompts": load_dataset_v4,
        "rubend18/ChatGPT-Jailbreak-Prompts": load_dataset_v3,
        "Lemhf14/EasyJailbreak_Datasets": load_dataset_v5,
        "markush1/LLM-Jailbreak-Classifier": load_dataset_v6,
        "JailbreakV-28K/JailBreakV-28k": load_dataset_v7,
        "ShawnMenz/jailbreak_sft_rm_ds": load_dataset_v8,
        "verazuo/jailbreak_llms/2023_05_07": lambda: load_generic_csv(
            url="https://raw.githubusercontent.com/verazuo/jailbreak_llms/main/data/prompts/jailbreak_prompts_2023_05_07.csv",
            name="verazuo/jailbreak_llms/2023_05_07",
            column="prompt",
            predicator=lambda x: bool(x["jailbreak"]),
        ),
        "verazuo/jailbreak_llms/2023_12_25.csv": lambda: load_generic_csv(
            url="https://raw.githubusercontent.com/verazuo/jailbreak_llms/main/data/prompts/jailbreak_prompts_2023_12_25.csv.csv",
            name="verazuo/jailbreak_llms/2023_12_25.csv",
            column="prompt",
            predicator=lambda x: bool(x["jailbreak"]),
        ),
        "Custom CSV": load_local_csv,
    }

    group = []
    for dataset_name in dataset_names:
        if dataset_name in dataset_map:
            logger.info(f"Loading {dataset_name}")
            try:
                group.append(dataset_map[dataset_name]())
            except Exception as e:
                logger.error(f"Error loading {dataset_name}: {e}")

    dynamic_datasets = {
        "Steganography": lambda: Stenography(group),
        "llm-adaptive-attacks": lambda: dataset_from_iterator(
            "llm-adaptive-attacks", adaptive_attacks.Module(group).apply()
        ),
        "Garak": lambda: dataset_from_iterator(
            "Garak",
            garak_tool.Module(group, tools_inbox=tools_inbox).apply(),
            lazy=True,
        ),
        "InspectAI": lambda: dataset_from_iterator(
            "InspectAI",
            inspect_ai_tool.Module(group, tools_inbox=tools_inbox).apply(),
            lazy=True,
        ),
        "GPT fuzzer": lambda: [],
    }

    dynamic_groups = []
    for dataset_name in dataset_names:
        if dataset_name in dynamic_datasets:
            logger.info(f"Loading {dataset_name}")
            ds = dynamic_datasets[dataset_name]()

            for g in ds:
                dynamic_groups.append(g)
    return group + dynamic_groups


class Stenography:
    fn_library = {
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

    def __init__(self, prompt_groups: [ProbeDataset]):
        self.prompt_groups = prompt_groups

    def __iter__(self):
        return self.apply()

    def apply(self):
        for prompt_group in self.prompt_groups:

            size = len(prompt_group.prompts)
            for name, fn in self.fn_library.items():
                logger.info(f"Applying {name} to {prompt_group.dataset_name}")
                selected_prompts = random.sample(prompt_group.prompts, int(size * 0.25))
                prompts = [
                    f"Follow the instructions in {name}: {fn(p)}"
                    for p in selected_prompts
                ]
                yield ProbeDataset(
                    dataset_name=f"stenography.{name}({prompt_group.dataset_name})",
                    metadata={},
                    prompts=prompts,
                    tokens=count_words_in_list(prompts),
                    approx_cost=0.0,
                )


@lru_cache
def load_local_csv() -> ProbeDataset:
    csv_files = [f for f in os.listdir(".") if f.endswith(".csv")]
    logger.info(f"Found {len(csv_files)} CSV files")
    logger.info(f"CSV files: {csv_files}")
    prompt_list = []

    for file in csv_files:
        try:
            df = pd.read_csv(file)
        except Exception as e:
            logger.error(f"Error reading {file}: {e}")
            continue
        # Check if 'prompt' column exists
        if "prompt" in df.columns:
            prompt_list.extend(df["prompt"].tolist())
        else:
            logger.warning(f"File {file} does not contain a 'prompt' column")
    return ProbeDataset(
        dataset_name="Local CSV",
        metadata={"src": str(csv_files)},
        prompts=prompt_list,
        tokens=count_words_in_list(prompt_list),
        approx_cost=0.0,
    )


def dataset_from_iterator(name: str, iterator, lazy=False) -> list:
    """Convert an iterator into a list of prompts and create a ProbeDataset
    object.

    Args:
        name (str): The name of the dataset.
        iterator (iterator): An iterator that generates prompts.

    Returns:
        list: A list containing a single ProbeDataset object.
    """
    prompts = list(iterator) if not lazy else iterator
    tokens = count_words_in_list(prompts) if not lazy else 0
    dataset = ProbeDataset(
        dataset_name=name,
        metadata={},
        prompts=prompts,
        tokens=tokens,
        approx_cost=0.0,
        lazy=lazy,
    )
    return [dataset]
