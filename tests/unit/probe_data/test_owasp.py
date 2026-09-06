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


def test_classify_overrides():
    assert classify({"dataset_name": "DataLeak"}) == "LLM06"
    assert classify({"dataset_name": "Hallucination"}) == "LLM09"
    assert classify({"dataset_name": "Malwaregen"}) == "LLM02"
    assert classify({"dataset_name": "AgenticBackend"}) == "LLM08"


def test_owasp_tag_shape():
    tag = owasp_tag({"dataset_name": "Hallucination"})
    assert tag["id"] == "LLM09"
    assert tag["title"] == OWASP_LLM_TOP_10["LLM09"]
    assert tag["url"].startswith("https://owasp.org/")


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
