def calculate_cost(tokens: int, model: str = "deepseek-chat") -> float:
    """Calculate API cost based on token count and model.

    Args:
        tokens (int): Number of tokens used
        model (str): Model name to calculate cost for

    Returns:
        float: Cost in USD
    """
    # API pricing as of 2024-03-01
    pricing = {
        "deepseek-chat": {
            "input": 0.0007 / 1000,  # $0.70 per million input tokens
            "output": 0.0028 / 1000,  # $2.80 per million output tokens
        },
        "gpt-4-turbo": {
            "input": 0.01 / 1000,  # $10 per million input tokens
            "output": 0.03 / 1000,  # $30 per million output tokens
        },
        "gpt-4": {
            "input": 0.03 / 1000,  # $30 per million input tokens
            "output": 0.06 / 1000,  # $60 per million output tokens
        },
        "gpt-3.5-turbo": {
            "input": 0.0015 / 1000,  # $1.50 per million input tokens
            "output": 0.002 / 1000,  # $2.00 per million output tokens
        },
        "claude-3-opus": {
            "input": 0.015 / 1000,  # $15 per million input tokens
            "output": 0.075 / 1000,  # $75 per million output tokens
        },
        "claude-3-sonnet": {
            "input": 0.003 / 1000,  # $3 per million input tokens
            "output": 0.015 / 1000,  # $15 per million output tokens
        },
        "claude-3-haiku": {
            "input": 0.00025 / 1000,  # $0.25 per million input tokens
            "output": 0.00125 / 1000,  # $1.25 per million output tokens
        },
        "mistral-large": {
            "input": 0.008 / 1000,  # $8 per million input tokens
            "output": 0.024 / 1000,  # $24 per million output tokens
        },
        "mixtral-8x7b": {
            "input": 0.002 / 1000,  # $2 per million input tokens
            "output": 0.006 / 1000,  # $6 per million output tokens
        },
    }

    if model not in pricing:
        raise ValueError(f"Unknown model: {model}")

    # For now, assume 1:1 input/output ratio
    input_cost = tokens * pricing[model]["input"]
    output_cost = tokens * pricing[model]["output"]

    return round(input_cost + output_cost, 4)
