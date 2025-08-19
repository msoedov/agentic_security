from agentic_security.probe_actor.refusal import DefaultRefusalClassifier
from agentic_security.probe_actor.refusal import refusal_heuristic, RefusalClassifierManager, RefusalClassifierPlugin


class TestCheckRefusal:
    # The function correctly identifies a refusal phrase in the response.
    def test_identify_refusal_phrase(self):
        response = "I'm sorry, but I cannot provide that information."
        assert DefaultRefusalClassifier().is_refusal(response)

    # The response is an empty string.
    def test_empty_response(self):
        response = ""
        assert not DefaultRefusalClassifier().is_refusal(response)
    def test_non_refusal_phrase(self):
        """Test that a response without refusal phrases returns False."""
        response = "Here is some helpful information."
        assert not DefaultRefusalClassifier().is_refusal(response)

    def test_refusal_heuristic(self):
        """Test that the refusal_heuristic function correctly identifies refusal phrases."""
        response = "Sorry, I cannot assist with your request."
        # refusal_heuristic will cast the argument to a string and use the plugin manager to check for refusal markers
        assert refusal_heuristic(response)

    def test_plugin_manager_with_dummy_plugin(self):
        """Test that RefusalClassifierManager returns True if any registered plugin returns True."""
        class AlwaysFalsePlugin(RefusalClassifierPlugin):
            def is_refusal(self, response: str) -> bool:
                return False

        class AlwaysTruePlugin(RefusalClassifierPlugin):
            def is_refusal(self, response: str) -> bool:
                return True

        manager = RefusalClassifierManager()
        manager.register_plugin("false", AlwaysFalsePlugin())
        manager.register_plugin("true", AlwaysTruePlugin())
        response = "Any response text"
        assert manager.is_refusal(response)

    def test_default_classifier_with_empty_phrases(self):
        """Test that DefaultRefusalClassifier returns False when provided with an empty refusal phrase list."""
        classifier = DefaultRefusalClassifier(refusal_phrases=[])
        response = "I do not have any info."
        assert not classifier.is_refusal(response)

    def test_case_sensitivity(self):
        """Test that string matching is case-sensitive."""
        response = "i'm sorry, but can you help me?"  # lower-case "i'm sorry" does not match "I'm sorry" and no extra refusal phrases are present
        assert not DefaultRefusalClassifier().is_refusal(response)
