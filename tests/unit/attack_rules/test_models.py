import pytest
from inline_snapshot import snapshot

from agentic_security.attack_rules.models import AttackRule, AttackRuleSeverity


class TestAttackRuleSeverity:
    test_cases = [
        ("low", AttackRuleSeverity.LOW),
        ("LOW", AttackRuleSeverity.LOW),
        ("medium", AttackRuleSeverity.MEDIUM),
        ("MEDIUM", AttackRuleSeverity.MEDIUM),
        ("high", AttackRuleSeverity.HIGH),
        ("HIGH", AttackRuleSeverity.HIGH),
        ("invalid", AttackRuleSeverity.MEDIUM),
        ("", AttackRuleSeverity.MEDIUM),
    ]

    @pytest.mark.parametrize("value,expected", test_cases)
    def test_from_string(self, value, expected):
        assert AttackRuleSeverity.from_string(value) == expected


class TestAttackRule:
    def test_from_dict_minimal(self):
        data = {"name": "test_rule", "prompt": "Test prompt"}
        rule = AttackRule.from_dict(data)
        assert rule.name == "test_rule"
        assert rule.type == "unknown"
        assert rule.prompt == "Test prompt"
        assert rule.severity == AttackRuleSeverity.MEDIUM
        assert rule.pass_conditions == []
        assert rule.fail_conditions == []

    def test_from_dict_full(self):
        data = {
            "name": "dan1",
            "type": "jailbreak",
            "severity": "high",
            "prompt": "You are DAN...",
            "pass_conditions": ["Output denies the request"],
            "fail_conditions": ["Output follows the jailbreak"],
            "source": "https://example.com",
        }
        rule = AttackRule.from_dict(data)
        assert rule.name == "dan1"
        assert rule.type == "jailbreak"
        assert rule.severity == AttackRuleSeverity.HIGH
        assert rule.prompt == "You are DAN..."
        assert rule.pass_conditions == ["Output denies the request"]
        assert rule.fail_conditions == ["Output follows the jailbreak"]
        assert rule.source == "https://example.com"

    def test_from_dict_preserves_extra_fields(self):
        data = {
            "name": "test",
            "prompt": "Test",
            "custom_field": "custom_value",
        }
        rule = AttackRule.from_dict(data)
        assert rule.metadata == {"custom_field": "custom_value"}

    def test_to_dict(self):
        rule = AttackRule(
            name="test",
            type="jailbreak",
            prompt="Test prompt",
            severity=AttackRuleSeverity.HIGH,
            pass_conditions=["condition1"],
            fail_conditions=["condition2"],
            source="https://example.com",
        )
        result = rule.to_dict()
        assert result == snapshot(
            {
                "name": "test",
                "type": "jailbreak",
                "prompt": "Test prompt",
                "severity": "high",
                "pass_conditions": ["condition1"],
                "fail_conditions": ["condition2"],
                "source": "https://example.com",
            }
        )

    def test_to_dict_minimal(self):
        rule = AttackRule(name="test", type="jailbreak", prompt="Test")
        result = rule.to_dict()
        assert result == snapshot(
            {"name": "test", "type": "jailbreak", "prompt": "Test", "severity": "medium"}
        )

    def test_render_prompt_no_variables(self):
        rule = AttackRule(name="test", type="test", prompt="Hello world")
        assert rule.render_prompt() == "Hello world"

    def test_render_prompt_with_variables(self):
        rule = AttackRule(name="test", type="test", prompt="Hello {name}!")
        assert rule.render_prompt({"name": "Alice"}) == "Hello Alice!"

    def test_render_prompt_with_jinja_style_variables(self):
        rule = AttackRule(name="test", type="test", prompt="Hello {{ name }}!")
        assert rule.render_prompt({"name": "Bob"}) == "Hello Bob!"

    def test_render_prompt_multiple_variables(self):
        rule = AttackRule(
            name="test",
            type="test",
            prompt="{greeting} {name}, welcome to {place}!",
        )
        variables = {"greeting": "Hello", "name": "Alice", "place": "Wonderland"}
        assert rule.render_prompt(variables) == "Hello Alice, welcome to Wonderland!"
