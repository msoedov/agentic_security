import pytest
from huggingface_hub import HfApi

from agentic_security.probe_data import REGISTRY

HF_DATASETS = [
    d
    for d in REGISTRY
    if "hugging" in d.get("source", "").lower() and d.get("is_active")
]


# Datasets get deleted or gated upstream; a dead REGISTRY entry silently drops
# probes from every scan. Metadata lookup only, so this stays fast (#72).
@pytest.mark.slow
@pytest.mark.parametrize("dataset", HF_DATASETS, ids=lambda d: d["dataset_name"])
def test_registry_dataset_reachable(dataset):
    info = HfApi().dataset_info(dataset["dataset_name"])
    assert info.id == dataset["dataset_name"]
    assert not info.disabled
