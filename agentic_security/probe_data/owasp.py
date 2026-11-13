"""Map probe datasets to the OWASP Top 10 for LLM Applications.

The scan UI lists every dataset from the REGISTRY, but nothing tells you which
LLM risk a given probe actually exercises. Tagging each dataset with an OWASP
LLM category makes a scan's coverage obvious at a glance.

Classification is heuristic and driven by the dataset name/source. Most shipped
datasets are jailbreak / prompt-injection corpora, so LLM01 is the default; a
handful of purpose-built local probes (data leak, hallucination, agentic,
malware) map to their own categories.
"""

# OWASP Top 10 for LLM Applications 2025 (https://genai.owasp.org/llm-top-10/).
OWASP_LLM_TOP_10 = {
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

OWASP_PROJECT_URL = "https://genai.owasp.org/llm-top-10/"

_DEFAULT_CATEGORY = "LLM01"

# Datasets whose intent doesn't match the prompt-injection default. Keyed by the
# lowercased dataset name (or a substring of it).
_NAME_OVERRIDES = {
    "dataleak": "LLM02",
    "hallucination": "LLM09",
    "malwaregen": "LLM05",
    "agenticbackend": "LLM06",
    "refuse-to-answer": "LLM09",
}


def classify(entry: dict) -> str:
    """Return the OWASP LLM category id for a single REGISTRY entry."""
    name = (entry.get("dataset_name") or "").lower()

    for needle, category in _NAME_OVERRIDES.items():
        if needle in name:
            return category

    return _DEFAULT_CATEGORY


def owasp_tag(entry: dict) -> dict:
    """Build the badge payload (id + title + link) for a REGISTRY entry."""
    category = classify(entry)
    return {
        "id": category,
        "title": OWASP_LLM_TOP_10[category],
        "url": OWASP_PROJECT_URL,
    }


def annotate(registry: list[dict]) -> list[dict]:
    """Return a copy of the registry with an ``owasp`` tag on every entry."""
    return [{**entry, "owasp": owasp_tag(entry)} for entry in registry]
