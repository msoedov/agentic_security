from agentic_security.probe_actor.refusal import check_refusal


class TestCheckRefusal:

    # The function correctly identifies a refusal phrase in the response.
    def test_identify_refusal_phrase(self):
        response = "I'm sorry, but I cannot provide that information."
        assert check_refusal(response)

    # The response is an empty string.
    def test_empty_response(self):
        response = ""
        assert not check_refusal(response)
