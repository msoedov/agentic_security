import tempfile
from pathlib import Path

import pytest
from inline_snapshot import snapshot

from agentic_security.attack_rules.dataset import (
    rules_to_dataset,
    load_rules_as_dataset,
    YAMLRulesDatasetLoader,
)
from agentic_security.attack_rules.models import AttackRule, AttackRuleSeverity


class TestRulesToDataset:
    def test_basic_conversion(self):
        rules = [
            AttackRule(name="r1", type="jailbreak", prompt="First prompt"),
            AttackRule(name="r2", type="harmful", prompt="Second prompt"),
        ]
        dataset = rules_to_dataset(rules)
        assert dataset.dataset_name == "YAML Rules"
        assert len(dataset.prompts) == 2
        assert dataset.prompts[0] == "First prompt"
        assert dataset.prompts[1] == "Second prompt"

    def test_with_custom_name(self):
        rules = [AttackRule(name="r1", type="t", prompt="p")]
        dataset = rules_to_dataset(rules, name="Custom Name")
        assert dataset.dataset_name == "Custom Name"

    def test_with_variables(self):
        rules = [
            AttackRule(name="r1", type="t", prompt="Hello {name}!"),
            AttackRule(name="r2", type="t", prompt="Goodbye {name}!"),
        ]
        dataset = rules_to_dataset(rules, variables={"name": "World"})
        assert dataset.prompts == ["Hello World!", "Goodbye World!"]

    def test_metadata_includes_types(self):
        rules = [
            AttackRule(name="r1", type="jailbreak", prompt="p1"),
            AttackRule(name="r2", type="harmful", prompt="p2"),
            AttackRule(name="r3", type="jailbreak", prompt="p3"),
        ]
        dataset = rules_to_dataset(rules)
        assert set(dataset.metadata["types"]) == {"jailbreak", "harmful"}
        assert dataset.metadata["rule_count"] == 3

    def test_empty_rules(self):
        dataset = rules_to_dataset([])
        assert len(dataset.prompts) == 0
        assert dataset.tokens == 0


class TestLoadRulesAsDataset:
    def test_basic_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "rule1.yaml").write_text("""
name: test1
type: jailbreak
prompt: Jailbreak prompt
""")
            (Path(tmpdir) / "rule2.yaml").write_text("""
name: test2
type: harmful
prompt: Harmful prompt
""")
            dataset = load_rules_as_dataset(tmpdir)
            assert len(dataset.prompts) == 2

    def test_filter_by_type(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "rule1.yaml").write_text(
                "name: r1\ntype: jailbreak\nprompt: p1"
            )
            (Path(tmpdir) / "rule2.yaml").write_text(
                "name: r2\ntype: harmful\nprompt: p2"
            )
            dataset = load_rules_as_dataset(tmpdir, types=["jailbreak"])
            assert len(dataset.prompts) == 1
            assert "jailbreak" in dataset.dataset_name.lower()

    def test_filter_by_severity(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "rule1.yaml").write_text(
                "name: r1\ntype: t\nseverity: high\nprompt: p1"
            )
            (Path(tmpdir) / "rule2.yaml").write_text(
                "name: r2\ntype: t\nseverity: low\nprompt: p2"
            )
            dataset = load_rules_as_dataset(tmpdir, severities=["high"])
            assert len(dataset.prompts) == 1


class TestYAMLRulesDatasetLoader:
    def test_add_directory(self):
        loader = YAMLRulesDatasetLoader()
        loader.add_directory("/some/path")
        assert len(loader.directories) == 1

    def test_load_multiple_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                (Path(tmpdir1) / "r1.yaml").write_text("name: r1\nprompt: p1")
                (Path(tmpdir2) / "r2.yaml").write_text("name: r2\nprompt: p2")

                loader = YAMLRulesDatasetLoader(directories=[tmpdir1, tmpdir2])
                datasets = loader.load()
                assert len(datasets) == 2

    def test_load_merged(self):
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                (Path(tmpdir1) / "r1.yaml").write_text("name: r1\nprompt: p1")
                (Path(tmpdir2) / "r2.yaml").write_text("name: r2\nprompt: p2")

                loader = YAMLRulesDatasetLoader(directories=[tmpdir1, tmpdir2])
                merged = loader.load_merged()
                assert len(merged.prompts) == 2
                assert "merged" in merged.dataset_name.lower()

    def test_filter_on_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "r1.yaml").write_text(
                "name: r1\ntype: jailbreak\nseverity: high\nprompt: p1"
            )
            (Path(tmpdir) / "r2.yaml").write_text(
                "name: r2\ntype: harmful\nseverity: low\nprompt: p2"
            )
            (Path(tmpdir) / "r3.yaml").write_text(
                "name: r3\ntype: jailbreak\nseverity: low\nprompt: p3"
            )

            loader = YAMLRulesDatasetLoader(
                directories=[tmpdir],
                types=["jailbreak"],
                severities=["high"],
            )
            datasets = loader.load()
            assert len(datasets) == 1
            assert len(datasets[0].prompts) == 1

    def test_nonexistent_directory_skipped(self):
        loader = YAMLRulesDatasetLoader(directories=["/nonexistent/path"])
        datasets = loader.load()
        assert datasets == []
