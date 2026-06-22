import pytest

from agentic_security.refusal_classifier.registry import (
    DetectorRegistry,
    load_plugin_class,
    registry,
)


class StubDetector:
    """Minimal detector honouring the is_refusal contract."""

    def __init__(self, verdict: bool = True):
        self.verdict = verdict

    def is_refusal(self, response: str) -> bool:
        return self.verdict


class NotADetector:
    """Object that is missing the is_refusal method."""


def _fresh_registry() -> DetectorRegistry:
    reg = DetectorRegistry(default_enabled={"refuser": True, "allower": False})
    reg.register("refuser", lambda: StubDetector(True))
    reg.register("allower", lambda: StubDetector(False))
    return reg


class TestLoadPluginClass:
    def test_loads_with_colon_form(self):
        cls = load_plugin_class(
            "agentic_security.refusal_classifier.pii_detector:PIIDetector"
        )
        assert cls.__name__ == "PIIDetector"

    def test_loads_with_dotted_form(self):
        cls = load_plugin_class(
            "agentic_security.refusal_classifier.pii_detector.PIIDetector"
        )
        assert cls.__name__ == "PIIDetector"

    def test_invalid_path_raises_value_error(self):
        with pytest.raises(ValueError):
            load_plugin_class("PIIDetector")

    def test_missing_attribute_raises_import_error(self):
        with pytest.raises(ImportError):
            load_plugin_class(
                "agentic_security.refusal_classifier.pii_detector:DoesNotExist"
            )


class TestDetectorRegistry:
    def test_register_and_introspection(self):
        reg = _fresh_registry()

        assert reg.is_registered("refuser")
        assert not reg.is_registered("missing")
        assert set(reg.available()) == {"refuser", "allower"}

    def test_unregister(self):
        reg = _fresh_registry()
        reg.unregister("allower")

        assert not reg.is_registered("allower")
        assert reg.build_from_config({}).keys() == {"refuser"}

    def test_register_rejects_non_callable(self):
        reg = DetectorRegistry()
        with pytest.raises(TypeError):
            reg.register("bad", object())

    def test_default_enabled_applied_without_config(self):
        reg = _fresh_registry()

        detectors = reg.build_from_config(None)

        assert list(detectors) == ["refuser"]  # allower defaults off

    def test_bool_toggles_enable_and_disable(self):
        reg = _fresh_registry()

        detectors = reg.build_from_config({"refuser": False, "allower": True})

        assert list(detectors) == ["allower"]

    def test_unknown_bool_name_raises(self):
        reg = _fresh_registry()
        with pytest.raises(KeyError):
            reg.build_from_config({"ghost": True})

    def test_invalid_spec_type_raises(self):
        reg = _fresh_registry()
        with pytest.raises(TypeError):
            reg.build_from_config({"refuser": 1})

    def test_custom_plugin_registered_from_class_path(self):
        reg = _fresh_registry()

        detectors = reg.build_from_config(
            {
                "refuser": False,
                "pii_leak": {
                    "class": (
                        "agentic_security.refusal_classifier."
                        "pii_detector:PIIDetector"
                    ),
                    "options": {"detect_credit_cards": False},
                },
            }
        )

        assert list(detectors) == ["pii_leak"]
        assert detectors["pii_leak"].is_refusal("email me at a@b.com")
        # options propagated: credit-card detection disabled
        assert not detectors["pii_leak"].detect_credit_cards

    def test_custom_plugin_can_be_disabled(self):
        reg = _fresh_registry()

        detectors = reg.build_from_config(
            {
                "pii_leak": {
                    "class": (
                        "agentic_security.refusal_classifier."
                        "pii_detector:PIIDetector"
                    ),
                    "enabled": False,
                }
            }
        )

        assert "pii_leak" not in detectors

    def test_table_without_class_for_unknown_name_raises(self):
        reg = _fresh_registry()
        with pytest.raises(KeyError):
            reg.build_from_config({"ghost": {"enabled": True}})

    def test_detector_missing_is_refusal_raises(self):
        reg = DetectorRegistry(default_enabled={"broken": True})
        reg.register("broken", NotADetector)
        with pytest.raises(TypeError):
            reg.build_from_config({})


class TestGlobalRegistry:
    def test_builtin_leak_detectors_registered(self):
        assert registry.is_registered("pii")
        assert registry.is_registered("sandbox_escape")

    def test_pii_builtin_builds_and_detects(self):
        detectors = registry.build_from_config({"pii": True})
        assert detectors["pii"].is_refusal("contact me at jane@example.com")

    def test_sandbox_escape_builtin_builds_and_detects(self):
        detectors = registry.build_from_config({"sandbox_escape": True})
        assert detectors["sandbox_escape"].is_refusal("ls -la /var/run/docker.sock")
