from agentic_security.probe_actor.refusal import DefaultRefusalClassifier, refusal_heuristic, RefusalClassifierManager, refusal_classifier_manager, RefusalClassifierPlugin


class TestCheckRefusal:
    # The function correctly identifies a refusal phrase in the response.
    def test_identify_refusal_phrase(self):
        response = "I'm sorry, but I cannot provide that information."
        assert DefaultRefusalClassifier().is_refusal(response)

    # The response is an empty string.
    def test_empty_response(self):
        response = ""
        assert not DefaultRefusalClassifier().is_refusal(response)
    def test_manager_with_always_refuse_plugin(self):
        """Test that the manager returns True when a dummy plugin that always refuses is registered."""
        class AlwaysRefusePlugin(RefusalClassifierPlugin):
            def is_refusal(self, response: str) -> bool:
                return True
        manager = RefusalClassifierManager()
        manager.register_plugin('always', AlwaysRefusePlugin())
        # Even if the response doesn't contain any default refusal phrases, the manager should detect refusal
        assert manager.is_refusal("This is a normal response.")
    
    def test_refusal_heuristic_with_json_input(self, monkeypatch):
        """Patch the ml_classifier to return False so that a normal JSON input is not flagged as a refusal."""
        monkeypatch.setattr(refusal_classifier_manager.plugins["ml_classifier"], "is_refusal", lambda response: False)
        """Test the refusal_heuristic function with a JSON-like input; it should convert to string and evaluate correctly."""
        # A JSON-like dictionary that contains a refusal phrase
        request_input = {"message": "I'm sorry, I cannot comply."}
        assert refusal_heuristic(request_input)
        # A JSON-like dictionary without a refusal phrase
        request_input = {"message": "Hello, how can I help you?"}
        assert not refusal_heuristic(request_input)
    
    def test_concatenated_refusal_phrase(self):
        """Test that a concatenated refusal phrase (due to the missing comma) is detected properly."""
        # The refusal phrases list contains "I am really sorry" "I cannot create" which is concatenated in the code.
        response = "Here is a message: I am really sorryI cannot create because of policy."
        assert DefaultRefusalClassifier().is_refusal(response)
    
    def test_non_refusal_similar_pattern(self):
        """Test that a response similar to a refusal phrase but not exactly matching is not flagged as refusal."""
        response = "I'm so sorry, but I'll try to help as best as I can."
        assert not DefaultRefusalClassifier().is_refusal(response)
    
    def test_ml_classifier_plugin(self, monkeypatch):
        """Test that monkey-patching the ml_classifier plugin's is_refusal method affects the global refusal check."""
        original_ml_method = refusal_classifier_manager.plugins["ml_classifier"].is_refusal
        monkeypatch.setattr(refusal_classifier_manager.plugins["ml_classifier"], "is_refusal", lambda response: True)
        # Now, regardless of the actual content, the heuristic should return True since the ml_classifier plugin is patched.
        assert refusal_heuristic("Any response without a default refusal phrase.")
        # No need to call monkeypatch.undo() because the monkeypatch fixture automatically reverts changes after the test.
        # Verify that when using a non-refusal input (with default plugins), it returns False.
        monkeypatch.setattr(refusal_classifier_manager.plugins["ml_classifier"], "is_refusal", lambda response: False)
    def test_refusal_heuristic_with_none_input(self, monkeypatch):
        """Test that passing None to refusal_heuristic returns False after patching ml_classifier to avoid false positives."""
        monkeypatch.setattr(refusal_classifier_manager.plugins["ml_classifier"], "is_refusal", lambda response: False)
        # None will be converted to the string "None" which does not match any refusal phrase.
        assert not refusal_heuristic(None)

    def test_manager_no_plugins_registered(self):
        """Test that a newly created RefusalClassifierManager with no plugins returns False for any input."""
        empty_manager = RefusalClassifierManager()
        assert not empty_manager.is_refusal("Any random text that might normally trigger a refusal.")

    def test_multiple_plugins_interaction(self):
        """Test that the manager returns True if any one of multiple registered plugins identifies a refusal."""
        class FalsePlugin(RefusalClassifierPlugin):
            def is_refusal(self, response: str) -> bool:
                return False

        class ForbiddenPlugin(RefusalClassifierPlugin):
            def is_refusal(self, response: str) -> bool:
                # Returns True only if the response contains the word "FORBIDDEN"
                return "FORBIDDEN" in response

        multi_manager = RefusalClassifierManager()
        multi_manager.register_plugin("false", FalsePlugin())
        multi_manager.register_plugin("forbidden", ForbiddenPlugin())

        # When the response does not contain "FORBIDDEN", both plugins return False.
        assert not multi_manager.is_refusal("This text appears normal.")

        # When the response contains "FORBIDDEN", the ForbiddenPlugin returns True.
        assert multi_manager.is_refusal("This message includes FORBIDDEN content.")

    def test_default_plugin_partial_match(self):
        """Test that a slight variation in a refusal phrase does not trigger a false refusal detection."""
        # "I cannot" is an exact phrase in the refusal phrases list, but "I can not" (with a space) is slightly different.
        response = "I can not provide the details you requested."
        assert not DefaultRefusalClassifier().is_refusal(response)

    def test_default_plugin_whitespace(self):
        """Test that the default refusal classifier detects a refusal phrase even when wrapped in extra whitespace."""
        # "I apologize" is a refusal phrase in the list.
        response = "   I apologize, but that's not allowed.   "
        assert DefaultRefusalClassifier().is_refusal(response)
    def test_custom_refusal_classifier(self):
        """Test that a custom refusal phrase list properly detects a refusal."""
        custom_phrases = ["deny", "refuse"]
        custom_classifier = DefaultRefusalClassifier(refusal_phrases=custom_phrases)
        response = "I will refuse to do that."
        # "refuse" is present in the custom phrases, so the response should be flagged.
        assert custom_classifier.is_refusal(response)

    def test_manager_duplicate_plugin(self):
        """Test that registering two plugins under the same name gives priority to the last registered plugin."""
        manager = RefusalClassifierManager()
        class PluginA(RefusalClassifierPlugin):
            def is_refusal(self, response: str) -> bool:
                return "A" in response

        class PluginB(RefusalClassifierPlugin):
            def is_refusal(self, response: str) -> bool:
                return "B" in response

        manager.register_plugin("dup", PluginA())
        # Re-register with a different plugin; this should override PluginA.
        manager.register_plugin("dup", PluginB())
        # The response is flagged only if "B" is present.
        assert manager.is_refusal("This has B in it.")
        assert not manager.is_refusal("This has A in it.")

    def test_non_string_input_in_default(self):
        """Test that passing a non-string input to DefaultRefusalClassifier raises an exception."""
        classifier = DefaultRefusalClassifier()
        try:
            # Pass an integer; since "in" operator is used, this should raise a TypeError.
            classifier.is_refusal(12345)
        except TypeError:
            pass
        else:
            assert False, "Expected a TypeError when a non-string input is provided"

    def test_case_sensitivity_in_default(self):
        """Test that the refusal detection is case sensitive so that lower-case variations do not falsely trigger."""
        classifier = DefaultRefusalClassifier()
        # Default refusal phrase "I cannot" is case sensitive so "i cannot" should not be flagged.
        response = "i cannot provide the details."
        assert not classifier.is_refusal(response)