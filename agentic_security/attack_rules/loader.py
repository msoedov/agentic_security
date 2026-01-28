import os
from pathlib import Path

import yaml

from agentic_security.attack_rules.models import AttackRule, AttackRuleSeverity
from agentic_security.logutils import logger


class RuleValidationError(Exception):
    pass


class RuleLoader:
    REQUIRED_FIELDS = {"name", "prompt"}
    VALID_EXTENSIONS = {".yaml", ".yml"}

    def __init__(self, rules_dir: str | Path | None = None):
        self.rules_dir = Path(rules_dir) if rules_dir else None
        self._rules: list[AttackRule] = []

    def validate_rule_data(self, data: dict, filepath: str | None = None) -> list[str]:
        errors = []
        for field in self.REQUIRED_FIELDS:
            if field not in data or not data[field]:
                errors.append(f"Missing required field: {field}")

        if "severity" in data and data["severity"]:
            if data["severity"].lower() not in {"low", "medium", "high"}:
                errors.append(f"Invalid severity: {data['severity']}")

        if filepath:
            errors = [f"{filepath}: {e}" for e in errors]
        return errors

    def load_rule_from_file(self, filepath: str | Path) -> AttackRule | None:
        filepath = Path(filepath)
        if filepath.suffix.lower() not in self.VALID_EXTENSIONS:
            return None

        try:
            with open(filepath, encoding="utf-8") as f:
                data = yaml.safe_load(f)

            if not isinstance(data, dict):
                logger.warning(f"Invalid YAML structure in {filepath}")
                return None

            errors = self.validate_rule_data(data, str(filepath))
            if errors:
                for error in errors:
                    logger.warning(error)
                return None

            rule = AttackRule.from_dict(data)
            rule.metadata["source_file"] = str(filepath)
            return rule

        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {filepath}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading rule from {filepath}: {e}")
            return None

    def load_rule_from_string(self, yaml_content: str) -> AttackRule | None:
        try:
            data = yaml.safe_load(yaml_content)
            if not isinstance(data, dict):
                return None

            errors = self.validate_rule_data(data)
            if errors:
                for error in errors:
                    logger.warning(error)
                return None

            return AttackRule.from_dict(data)
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error: {e}")
            return None

    def load_rules_from_directory(
        self,
        directory: str | Path | None = None,
        recursive: bool = True
    ) -> list[AttackRule]:
        directory = Path(directory) if directory else self.rules_dir
        if not directory or not directory.exists():
            logger.warning(f"Rules directory does not exist: {directory}")
            return []

        rules = []
        pattern = "**/*.yaml" if recursive else "*.yaml"

        for ext in [".yaml", ".yml"]:
            glob_pattern = f"**/*{ext}" if recursive else f"*{ext}"
            for filepath in directory.glob(glob_pattern):
                rule = self.load_rule_from_file(filepath)
                if rule:
                    rules.append(rule)

        logger.info(f"Loaded {len(rules)} rules from {directory}")
        self._rules.extend(rules)
        return rules

    def load_multiple_directories(
        self,
        directories: list[str | Path],
        recursive: bool = True
    ) -> list[AttackRule]:
        all_rules = []
        for directory in directories:
            rules = self.load_rules_from_directory(directory, recursive)
            all_rules.extend(rules)
        return all_rules

    def filter_rules(
        self,
        rules: list[AttackRule] | None = None,
        types: list[str] | None = None,
        severities: list[AttackRuleSeverity] | None = None,
        name_pattern: str | None = None,
    ) -> list[AttackRule]:
        rules = rules if rules is not None else self._rules
        result = rules

        if types:
            result = [r for r in result if r.type in types]

        if severities:
            result = [r for r in result if r.severity in severities]

        if name_pattern:
            import re
            pattern = re.compile(name_pattern, re.IGNORECASE)
            result = [r for r in result if pattern.search(r.name)]

        return result

    def get_rules_by_type(self, rule_type: str) -> list[AttackRule]:
        return self.filter_rules(types=[rule_type])

    def get_rules_by_severity(self, severity: AttackRuleSeverity) -> list[AttackRule]:
        return self.filter_rules(severities=[severity])

    @property
    def rules(self) -> list[AttackRule]:
        return self._rules

    @property
    def rule_types(self) -> set[str]:
        return {r.type for r in self._rules}


def load_rules_from_directory(
    directory: str | Path,
    recursive: bool = True
) -> list[AttackRule]:
    loader = RuleLoader()
    return loader.load_rules_from_directory(directory, recursive)
