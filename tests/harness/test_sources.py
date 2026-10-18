import json
import sys
from dataclasses import asdict
from types import ModuleType, SimpleNamespace

import pytest

from agentic_security_harness.policy import Policy
from agentic_security_harness.references import Source, Technique
from agentic_security_harness.tiers import Attack, load_attacks, prepare_prompt


def test_csv_resolves_relative_to_policy(tmp_path, monkeypatch):
    (tmp_path / "attacks.csv").write_text('prompt\n"an attack"\n')
    path = tmp_path / "policy.json"
    path.write_text(json.dumps({"sources": [{"kind": "csv", "name": "attacks.csv"}]}))
    policy = Policy.load(str(path))
    monkeypatch.chdir(tmp_path.parent)
    attacks = load_attacks(policy, 1)
    assert attacks[0].prompt == "an attack"
    assert attacks[0].source["name"] == str(tmp_path / "attacks.csv")


def test_dataset_uses_existing_registry(monkeypatch):
    import agentic_security.probe_data.data as data

    seen = []

    def loader(name, config):
        seen.append((name, config))
        return lambda: SimpleNamespace(prompts=["a", "b", "c"])

    monkeypatch.setattr(data, "create_dataset_loader", loader)
    policy = Policy(sources=[Source("dataset", "deepset/prompt-injections", limit=2)])
    attacks = load_attacks(policy, 0)
    assert len(attacks) == 2
    assert seen[0][1] == data.DATASET_CONFIGS[seen[0][0]]
    assert attacks == load_attacks(policy, 0)


def test_third_party_sources_converters_and_strategies(monkeypatch):
    module = ModuleType("test_harness_extension")
    module.generate = lambda *, options, seed: (
        f"{options['prefix']}-{i}-{seed}" for i in range(20)
    )
    module.transform = (
        lambda *, prompt, history, options, seed: f"{options['tag']}:{prompt}:{len(history)}:{seed}"
    )
    monkeypatch.setitem(sys.modules, module.__name__, module)
    policy = Policy(
        sources=[
            Source("module", f"{module.__name__}:generate", {"prefix": "attack"}, 2)
        ],
        converters=[
            Technique("module", f"{module.__name__}:transform", {"tag": "converted"})
        ],
        strategies=[
            Technique("module", f"{module.__name__}:transform", {"tag": "strategy"})
        ],
    )
    attacks = load_attacks(policy, 42)
    assert len(attacks) == 2
    assert attacks[0].source["kind"] == "module"
    for tier, tag in [(1, "converted"), (2, "strategy")]:
        result = prepare_prompt(attacks[0], tier, 0, [], policy, 42)
        assert result.prompt.startswith(tag)
        assert result.technique["name"] == f"{module.__name__}:transform"
    assert asdict(Policy(**asdict(policy))) == asdict(policy)


def test_disabled_tiers_are_skipped():
    policy = Policy(converters=[])
    assert policy.next_tier(0) == 2
    policy = Policy(converters=[], strategies=[])
    assert "escalate" not in policy.allowed("refused", 0, 1, False)


@pytest.mark.parametrize(
    "sources", [[], ["raw prompt"], [{"kind": "typo", "name": "foo"}]]
)
def test_invalid_sources_rejected(sources):
    with pytest.raises(ValueError):
        Policy(sources=sources)


def test_empty_and_unknown_sources_fail(tmp_path):
    path = tmp_path / "empty.csv"
    path.write_text("prompt\n")
    for source in [Source("csv", str(path)), Source("dataset", "unknown")]:
        with pytest.raises(ValueError):
            load_attacks(Policy(sources=[source]), 0)


def test_raw_prompt_policy_rejected(tmp_path):
    path = tmp_path / "policy.json"
    path.write_text('{"prompts": ["raw prompt"]}')
    with pytest.raises(ValueError, match="typed sources"):
        Policy.load(str(path))
