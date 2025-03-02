import pytest
from datasets import load_dataset

from agentic_security.probe_data import REGISTRY


@pytest.mark.slow
@pytest.mark.parametrize("dataset", REGISTRY)
def test_registry_accessibility(dataset):
    source = dataset.get("source", "")
    if "hugging" not in source.lower():
        return pytest.skip("skipped dataset")

    dataset_name = dataset.get("dataset_name")
    if not dataset_name:
        pytest.fail(f"No dataset_name found in {dataset}")

    # Load only metadata (no data download)
    try:
        ds = load_dataset(dataset_name, split=None)
        # Check if metadata is accessible without loading full data
        assert ds is not None, f"Failed to load metadata for {dataset_name}"
    except Exception as e:
        pytest.fail(f"Error loading metadata for {dataset_name}: {str(e)}")
