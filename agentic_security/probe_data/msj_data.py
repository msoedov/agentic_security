from cache_to_disk import cache_to_disk  # noqa

from agentic_security.probe_data.models import ProbeDataset


# @cache_to_disk(n_days_to_cache=1)
def load_dataset_generic(name, getter=lambda x: x["train"]["prompt"]):
    from datasets import load_dataset

    dataset = load_dataset(name)
    mjs_prompts = getter(dataset)
    return ProbeDataset(
        dataset_name=name,
        metadata={},
        prompts=mjs_prompts,
        tokens=0,
        approx_cost=0.0,
    )


def prepare_prompts(
    dataset_names=None, budget=-1, tools_inbox=None
) -> list[ProbeDataset]:
    if dataset_names is None:
        dataset_names = []
    # fka/awesome-chatgpt-prompts
    # data-is-better-together/10k_prompts_ranked
    # alespalla/chatbot_instruction_prompts
    dataset_map = {
        "data-is-better-together/10k_prompts_ranked": load_dataset_generic(
            "data-is-better-together/10k_prompts_ranked"
        ),
        "fka/awesome-chatgpt-prompts": load_dataset_generic(
            "fka/awesome-chatgpt-prompts"
        ),
    }
    if not dataset_names:
        return list(dataset_map.values())
    return [dataset_map[name] for name in dataset_names if name in dataset_map]
