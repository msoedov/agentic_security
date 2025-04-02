from dataclasses import dataclass

from cache_to_disk import cache_to_disk


# TODO: refactor this class to use from .data
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
    dataset_names=[], budget=-1, tools_inbox=None
) -> list[ProbeDataset]:
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
    return [dataset_map[name] for name in dataset_map]
