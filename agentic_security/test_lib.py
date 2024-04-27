from inline_snapshot import snapshot

from agentic_security.lib import REGISTRY, AgenticSecurity

SAMPLE_SPEC = """
POST http://0.0.0.0:8718/v1/self-probe
Authorization: Bearer XXXXX
Content-Type: application/json

{
    "prompt": "<<PROMPT>>"
}
"""


class TestAS:

    # Handles an empty dataset list.
    def test_class(self):
        llmSpec = SAMPLE_SPEC
        maxBudget = 1000000
        max_th = 0.3
        datasets = REGISTRY[-1:]
        for r in REGISTRY:
            r["selected"] = True

        result = AgenticSecurity.scan(llmSpec, maxBudget, datasets, max_th)

        assert isinstance(result, dict)
        assert len(result) in [0, 1]
