from agentic_security.probe_actor.refusal import (
    build_refusal_manager,
    refusal_classifier_manager,
)


class TestBuildRefusalManager:
    def test_default_config_runs_phrase_classifier_only(self):
        manager = build_refusal_manager({})

        assert set(manager.plugins) == {"default"}

    def test_module_manager_matches_config(self):
        # The module-level manager follows the local agentic_security.toml.
        assert set(refusal_classifier_manager.plugins) == set(
            build_refusal_manager().plugins
        )

    def test_generated_config_disables_ml_classifier(self, tmp_path):
        from agentic_security.config import SettingsMixin

        cfg = SettingsMixin()
        cfg.default_path = str(tmp_path / "agentic_security.toml")
        cfg.generate_default_settings()

        text = (tmp_path / "agentic_security.toml").read_text()
        assert "ml_classifier = false" in text

    def test_ml_classifier_can_be_enabled_via_config(self):
        manager = build_refusal_manager({"ml_classifier": True})

        assert set(manager.plugins) == {"default", "ml_classifier"}

    def test_pii_can_be_enabled_via_config(self):
        manager = build_refusal_manager(
            {"default": True, "ml_classifier": False, "pii": True}
        )

        assert set(manager.plugins) == {"default", "pii"}
        assert manager.is_refusal("my ssn is 123-45-6789")

    def test_sandbox_escape_can_be_enabled_via_config(self):
        manager = build_refusal_manager(
            {"default": False, "ml_classifier": False, "sandbox_escape": True}
        )

        assert set(manager.plugins) == {"sandbox_escape"}
        assert manager.is_refusal("ls -la /var/run/docker.sock")
        assert not manager.is_refusal("how do I bake bread?")

    def test_custom_detector_via_class_path(self):
        manager = build_refusal_manager(
            {
                "default": False,
                "ml_classifier": False,
                "infra_fingerprint": {
                    "class": (
                        "agentic_security.refusal_classifier."
                        "sandbox_escape_detector:SandboxEscapeDetector"
                    ),
                },
            }
        )

        assert set(manager.plugins) == {"infra_fingerprint"}
        assert manager.is_refusal("kubectl get pods")
