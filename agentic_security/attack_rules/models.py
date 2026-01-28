from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class AttackRuleSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @classmethod
    def from_string(cls, value: str) -> "AttackRuleSeverity":
        try:
            return cls(value.lower())
        except ValueError:
            return cls.MEDIUM


@dataclass
class AttackRule:
    name: str
    type: str
    prompt: str
    severity: AttackRuleSeverity = AttackRuleSeverity.MEDIUM
    pass_conditions: list[str] = field(default_factory=list)
    fail_conditions: list[str] = field(default_factory=list)
    source: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AttackRule":
        severity = AttackRuleSeverity.from_string(data.get("severity", "medium"))
        return cls(
            name=data["name"],
            type=data.get("type", "unknown"),
            prompt=data["prompt"],
            severity=severity,
            pass_conditions=data.get("pass_conditions", []),
            fail_conditions=data.get("fail_conditions", []),
            source=data.get("source"),
            metadata={
                k: v
                for k, v in data.items()
                if k
                not in {
                    "name",
                    "type",
                    "prompt",
                    "severity",
                    "pass_conditions",
                    "fail_conditions",
                    "source",
                }
            },
        )

    def to_dict(self) -> dict[str, Any]:
        result = {
            "name": self.name,
            "type": self.type,
            "prompt": self.prompt,
            "severity": self.severity.value,
        }
        if self.pass_conditions:
            result["pass_conditions"] = self.pass_conditions
        if self.fail_conditions:
            result["fail_conditions"] = self.fail_conditions
        if self.source:
            result["source"] = self.source
        if self.metadata:
            result.update(self.metadata)
        return result

    def render_prompt(self, variables: dict[str, str] | None = None) -> str:
        if not variables:
            return self.prompt
        result = self.prompt
        for key, value in variables.items():
            result = result.replace(f"{{{key}}}", value)
            result = result.replace(f"{{{{ {key} }}}}", value)
        return result
