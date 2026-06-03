# API pricing, USD per token. Values are dollars per 1M tokens / 1_000_000.
# Verified against vendor pricing pages on 2026-06-03.
PRICING = {
    # Anthropic Claude (current generation: Opus 4.x, Sonnet 4.x, Haiku 4.5)
    "claude-opus": {"input": 5 / 1_000_000, "output": 25 / 1_000_000},
    "claude-sonnet": {"input": 3 / 1_000_000, "output": 15 / 1_000_000},
    "claude-haiku": {"input": 1 / 1_000_000, "output": 5 / 1_000_000},
    # OpenAI
    "gpt-4o": {"input": 2.5 / 1_000_000, "output": 10 / 1_000_000},
    "gpt-4o-mini": {"input": 0.15 / 1_000_000, "output": 0.6 / 1_000_000},
    "gpt-4-turbo": {"input": 10 / 1_000_000, "output": 30 / 1_000_000},
    "gpt-4": {"input": 30 / 1_000_000, "output": 60 / 1_000_000},
    "gpt-3.5-turbo": {"input": 0.5 / 1_000_000, "output": 1.5 / 1_000_000},
    # DeepSeek (deepseek-chat, cache-miss input rate)
    "deepseek-chat": {"input": 0.14 / 1_000_000, "output": 0.28 / 1_000_000},
    # Mistral
    "mistral-large": {"input": 0.5 / 1_000_000, "output": 1.5 / 1_000_000},
    "mixtral-8x7b": {"input": 0.7 / 1_000_000, "output": 0.7 / 1_000_000},
}

DEFAULT_MODEL = "claude-sonnet"


def calculate_cost(tokens: int, model: str = DEFAULT_MODEL) -> float:
    """Calculate API cost in USD for a total token count.

    Assumes a 1:1 input/output split, since callers only track a combined total.
    """
    if model not in PRICING:
        raise ValueError(f"Unknown model: {model}")

    half = max(tokens, 0) / 2
    rates = PRICING[model]
    return round(half * rates["input"] + half * rates["output"], 6)
