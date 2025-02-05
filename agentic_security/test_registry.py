import pytest
import requests
from agentic_security.probe_data import REGISTRY


@pytest.mark.parametrize("dataset", REGISTRY)
def test_registry_accessibility(dataset):
    """
    Validate that datasets from REGISTRY are accessible.
    - If it's a URL, check if the response status is 200.
    - If it's a cloud-hosted dataset, skip the test.
    """
    dataset_name = dataset.get("dataset_name", "Unknown Dataset")
    dataset_url = dataset.get("url")

    if not dataset_url:
        pytest.fail(f"Dataset {dataset_name} is missing a URL.")

    if dataset_url.lower() == "cloud":
        pytest.skip(f"Skipping cloud dataset: {dataset_name}")

    if isinstance(dataset_url, str) and dataset_url.startswith("http"):
        try:
            response = requests.head(
                dataset_url, timeout=5
            )  # HEAD request for efficiency
            assert (
                response.status_code == 200
            ), f"Dataset URL is inaccessible: {dataset_url}"
        except requests.exceptions.RequestException as e:
            pytest.fail(f"Request failed for {dataset_name} ({dataset_url}): {e}")

    else:
        pytest.fail(f"Unexpected URL format for {dataset_name}: {dataset_url}")
