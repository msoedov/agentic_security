from agentic_security.probe_actor.refusal import (
    build_refusal_manager,
    refusal_classifier_manager,
)


class TestBuildRefusalManager:
    def test_default_config_preserves_legacy_plugins(self):
        manager = build_refusal_manager({})

        assert set(manager.plugins) == {"default", "ml_classifier"}

    def test_module_manager_matches_default(self):
        assert set(refusal_classifier_manager.plugins) == {"default", "ml_classifier"}

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
