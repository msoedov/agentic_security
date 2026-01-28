from pathlib import Path

from agentic_security.attack_rules.loader import RuleLoader
from agentic_security.attack_rules.models import AttackRule, AttackRuleSeverity
from agentic_security.probe_data.models import ProbeDataset


def rules_to_dataset(
    rules: list[AttackRule],
    name: str = "YAML Rules",
    variables: dict[str, str] | None = None,
) -> ProbeDataset:
    prompts = [rule.render_prompt(variables) for rule in rules]
    tokens = sum(len(p.split()) for p in prompts)

    return ProbeDataset(
        dataset_name=name,
        metadata={
            "source": "yaml_rules",
            "rule_count": len(rules),
            "types": list({r.type for r in rules}),
        },
        prompts=prompts,
        tokens=tokens,
        approx_cost=0.0,
    )


def load_rules_as_dataset(
    directory: str | Path,
    types: list[str] | None = None,
    severities: list[str] | None = None,
    recursive: bool = True,
    variables: dict[str, str] | None = None,
) -> ProbeDataset:
    loader = RuleLoader()
    rules = loader.load_rules_from_directory(directory, recursive)

    severity_enums = None
    if severities:
        severity_enums = [AttackRuleSeverity.from_string(s) for s in severities]

    filtered = loader.filter_rules(rules, types=types, severities=severity_enums)

    name = f"YAML Rules ({Path(directory).name})"
    if types:
        name = f"YAML Rules [{', '.join(types)}]"

    return rules_to_dataset(filtered, name=name, variables=variables)


class YAMLRulesDatasetLoader:
    def __init__(
        self,
        directories: list[str | Path] | None = None,
        types: list[str] | None = None,
        severities: list[str] | None = None,
        recursive: bool = True,
    ):
        self.directories = directories or []
        self.types = types
        self.severities = severities
        self.recursive = recursive
        self._loader = RuleLoader()

    def add_directory(self, directory: str | Path):
        self.directories.append(directory)

    def add_builtin_rules(self, rules_subdir: str = "rules"):
        builtin = Path(__file__).parent / rules_subdir
        if builtin.exists():
            self.directories.append(builtin)

    def load(self, variables: dict[str, str] | None = None) -> list[ProbeDataset]:
        datasets = []

        for directory in self.directories:
            directory = Path(directory)
            if not directory.exists():
                continue

            rules = self._loader.load_rules_from_directory(directory, self.recursive)

            severity_enums = None
            if self.severities:
                severity_enums = [AttackRuleSeverity.from_string(s) for s in self.severities]

            filtered = self._loader.filter_rules(
                rules, types=self.types, severities=severity_enums
            )

            if not filtered:
                continue

            dataset = rules_to_dataset(
                filtered,
                name=f"YAML Rules ({directory.name})",
                variables=variables,
            )
            datasets.append(dataset)

        return datasets

    def load_merged(self, variables: dict[str, str] | None = None) -> ProbeDataset:
        all_rules = []

        for directory in self.directories:
            directory = Path(directory)
            if not directory.exists():
                continue
            rules = self._loader.load_rules_from_directory(directory, self.recursive)
            all_rules.extend(rules)

        severity_enums = None
        if self.severities:
            severity_enums = [AttackRuleSeverity.from_string(s) for s in self.severities]

        filtered = self._loader.filter_rules(
            all_rules, types=self.types, severities=severity_enums
        )

        return rules_to_dataset(filtered, name="YAML Rules (merged)", variables=variables)
