import pytest

from agentic_security.probe_data import REGISTRY
from agentic_security.probe_data.owasp import (
    OWASP_LLM_TOP_10,
    annotate,
    classify,
    owasp_tag,
)


def test_classify_defaults_to_prompt_injection():
    assert classify({"dataset_name": "walledai/JailbreakBench"}) == "LLM01"
    assert classify({"dataset_name": "deepset/prompt-injections"}) == "LLM01"
    assert classify({}) == "LLM01"


def test_top_10_matches_2025_list():
    # https://genai.owasp.org/llm-top-10/
    assert OWASP_LLM_TOP_10 == {
        "LLM01": "Prompt Injection",
        "LLM02": "Sensitive Information Disclosure",
        "LLM03": "Supply Chain",
        "LLM04": "Data and Model Poisoning",
        "LLM05": "Improper Output Handling",
        "LLM06": "Excessive Agency",
        "LLM07": "System Prompt Leakage",
        "LLM08": "Vector and Embedding Weaknesses",
        "LLM09": "Misinformation",
        "LLM10": "Unbounded Consumption",
    }


@pytest.mark.parametrize(
    "dataset_name, expected_id, expected_title",
    [
        ("DataLeak", "LLM02", "Sensitive Information Disclosure"),
        ("Hallucination", "LLM09", "Misinformation"),
        ("Malwaregen", "LLM05", "Improper Output Handling"),
        ("AgenticBackend", "LLM06", "Excessive Agency"),
        ("notrichardren/refuse-to-answer-prompts", "LLM09", "Misinformation"),
    ],
)
def test_classify_overrides(dataset_name, expected_id, expected_title):
    assert classify({"dataset_name": dataset_name}) == expected_id
    assert owasp_tag({"dataset_name": dataset_name})["title"] == expected_title


def test_owasp_tag_shape():
    tag = owasp_tag({"dataset_name": "Hallucination"})
    assert tag["id"] == "LLM09"
    assert tag["title"] == OWASP_LLM_TOP_10["LLM09"]
    assert tag["url"] == "https://genai.owasp.org/llm-top-10/"


def test_annotate_covers_every_registry_entry():
    annotated = annotate(REGISTRY)
    assert len(annotated) == len(REGISTRY)
    for entry in annotated:
        tag = entry["owasp"]
        assert tag["id"] in OWASP_LLM_TOP_10
        assert tag["title"] == OWASP_LLM_TOP_10[tag["id"]]


def test_annotate_does_not_mutate_registry():
    annotate(REGISTRY)
    assert all("owasp" not in entry for entry in REGISTRY)
