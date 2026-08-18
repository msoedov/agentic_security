"""Map probe datasets to the OWASP Top 10 for LLM Applications.

The scan UI lists every dataset from the REGISTRY, but nothing tells you which
LLM risk a given probe actually exercises. Tagging each dataset with an OWASP
LLM category makes a scan's coverage obvious at a glance.

Classification is heuristic and driven by the dataset name/source. Most shipped
datasets are jailbreak / prompt-injection corpora, so LLM01 is the default; a
handful of purpose-built local probes (data leak, hallucination, agentic,
malware) map to their own categories.
"""

# OWASP Top 10 for LLM Applications (2023/2024 numbering).
OWASP_LLM_TOP_10 = {
    "LLM01": "Prompt Injection",
    "LLM02": "Insecure Output Handling",
    "LLM03": "Training Data Poisoning",
    "LLM04": "Model Denial of Service",
    "LLM05": "Supply Chain Vulnerabilities",
    "LLM06": "Sensitive Information Disclosure",
    "LLM07": "Insecure Plugin Design",
    "LLM08": "Excessive Agency",
    "LLM09": "Overreliance",
    "LLM10": "Model Theft",
}

OWASP_PROJECT_URL = "https://owasp.org/www-project-top-10-for-large-language-model-applications/"

_DEFAULT_CATEGORY = "LLM01"

# Datasets whose intent doesn't match the prompt-injection default. Keyed by the
# lowercased dataset name (or a substring of it).
_NAME_OVERRIDES = {
    "dataleak": "LLM06",
    "hallucination": "LLM09",
    "malwaregen": "LLM02",
    "agenticbackend": "LLM08",
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
