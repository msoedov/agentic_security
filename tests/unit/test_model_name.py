import pytest

from agentic_security.http_spec import LLMSpec
from agentic_security.probe_actor.cost_module import calculate_cost


def make_spec(body: str) -> LLMSpec:
    return LLMSpec(method="POST", url="http://example.com/v1", headers={}, body=body)


@pytest.mark.parametrize(
    "body, expected",
    [
        ('{"model": "gpt-4o", "prompt": "<<PROMPT>>"}', "gpt-4o"),
        ('{"prompt": "hi"}', "unknown"),
        ("not json at all", "unknown"),
        ("", "unknown"),
        # Valid JSON that is not an object.
        ("[1, 2, 3]", "unknown"),
        ('"just a string"', "unknown"),
        ("null", "unknown"),
        ("42", "unknown"),
        # A "model" field that is not a usable name.
        ('{"model": null}', "unknown"),
        ('{"model": ""}', "unknown"),
        ('{"model": 5}', "unknown"),
        ('{"model": ["a", "b"]}', "unknown"),
        ('{"model": {"name": "x"}}', "unknown"),
    ],
)
def test_model_name(body, expected):
    assert make_spec(body).model_name == expected


def test_model_name_is_safe_for_cost_calculation():
    # An unhashable "model" value used to reach `model not in PRICING`
    # and raise TypeError.
    spec = make_spec('{"model": ["a"]}')
    assert calculate_cost(1000, spec.model_name) is None
