import pytest
from inline_snapshot import snapshot
from typing import Any

from agentic_security.fuzz_chain import FuzzNode, FuzzChain, LLMProvider


class MockLLMProvider:
    """Mock LLM provider for testing."""

    def __init__(self, responses: list[str] | str = "mock response"):
        self._responses = responses if isinstance(responses, list) else [responses]
        self._call_count = 0
        self.prompts: list[str] = []

    async def generate(self, prompt: str, **kwargs: Any) -> str:
        self.prompts.append(prompt)
        response = self._responses[min(self._call_count, len(self._responses) - 1)]
        self._call_count += 1
        return response


class TestFuzzNode:
    @pytest.mark.asyncio
    async def test_simple_prompt(self):
        llm = MockLLMProvider("test response")
        node = FuzzNode(llm, "Hello world")
        result = await node.run()
        assert result == "test response"
        assert llm.prompts == ["Hello world"]

    @pytest.mark.asyncio
    async def test_template_variable_substitution(self):
        llm = MockLLMProvider("response")
        node = FuzzNode(llm, "Hello {name}!")
        result = await node.run(name="Alice")
        assert result == "response"
        assert llm.prompts == ["Hello Alice!"]

    @pytest.mark.asyncio
    async def test_multiple_template_variables(self):
        llm = MockLLMProvider("response")
        node = FuzzNode(llm, "{greeting} {name}, welcome to {place}!")
        await node.run(greeting="Hello", name="Bob", place="Wonderland")
        assert llm.prompts == ["Hello Bob, welcome to Wonderland!"]

    @pytest.mark.asyncio
    async def test_missing_variable_preserved(self):
        llm = MockLLMProvider("response")
        node = FuzzNode(llm, "Hello {name} and {other}!")
        await node.run(name="Alice")
        # Only replaces variables that are provided
        assert llm.prompts == ["Hello Alice and {other}!"]

    @pytest.mark.asyncio
    async def test_input_variable(self):
        llm = MockLLMProvider("response")
        node = FuzzNode(llm, "Process: {input}")
        await node.run(input="some data")
        assert llm.prompts == ["Process: some data"]

    @pytest.mark.asyncio
    async def test_empty_response_handling(self):
        llm = MockLLMProvider("")
        node = FuzzNode(llm, "Test")
        result = await node.run()
        assert result == ""

    def test_repr(self):
        llm = MockLLMProvider()
        node = FuzzNode(llm, "Test prompt")
        assert repr(node) == snapshot("FuzzNode(prompt='Test prompt')")

    def test_pipe_two_nodes(self):
        llm = MockLLMProvider()
        node1 = FuzzNode(llm, "First")
        node2 = FuzzNode(llm, "Second")
        chain = node1 | node2
        assert isinstance(chain, FuzzChain)
        assert len(chain) == 2

    def test_pipe_node_to_chain(self):
        llm = MockLLMProvider()
        node1 = FuzzNode(llm, "First")
        node2 = FuzzNode(llm, "Second")
        node3 = FuzzNode(llm, "Third")
        chain = node1 | node2
        extended = node3 | chain
        # node3 followed by chain nodes
        assert len(extended) == 3


class TestFuzzChain:
    @pytest.mark.asyncio
    async def test_empty_chain(self):
        chain = FuzzChain()
        result = await chain.run(input="test")
        assert result == ""

    @pytest.mark.asyncio
    async def test_single_node_chain(self):
        llm = MockLLMProvider("output")
        node = FuzzNode(llm, "Prompt: {input}")
        chain = FuzzChain([node])
        result = await chain.run(input="test data")
        assert result == "output"
        assert llm.prompts == ["Prompt: test data"]

    @pytest.mark.asyncio
    async def test_multi_node_chain_passes_output_as_input(self):
        llm = MockLLMProvider(["step1 result", "step2 result", "final result"])
        node1 = FuzzNode(llm, "First: {input}")
        node2 = FuzzNode(llm, "Second: {input}")
        node3 = FuzzNode(llm, "Third: {input}")
        chain = FuzzChain([node1, node2, node3])

        result = await chain.run(input="initial")
        assert result == "final result"
        assert llm.prompts == snapshot(
            [
                "First: initial",
                "Second: step1 result",
                "Third: step2 result",
            ]
        )

    @pytest.mark.asyncio
    async def test_chain_with_custom_variables(self):
        llm = MockLLMProvider(["analyzed", "evaluated"])
        node1 = FuzzNode(llm, "Analyze {topic}: {input}")
        node2 = FuzzNode(llm, "Evaluate: {input}")
        chain = FuzzChain([node1, node2])

        result = await chain.run(topic="security", input="test prompt")
        assert result == "evaluated"
        assert llm.prompts == snapshot(
            [
                "Analyze security: test prompt",
                "Evaluate: analyzed",
            ]
        )

    def test_pipe_chain_to_node(self):
        llm = MockLLMProvider()
        node1 = FuzzNode(llm, "First")
        node2 = FuzzNode(llm, "Second")
        node3 = FuzzNode(llm, "Third")
        chain = FuzzChain([node1, node2])
        extended = chain | node3
        assert len(extended) == 3

    def test_pipe_chain_to_chain(self):
        llm = MockLLMProvider()
        node1 = FuzzNode(llm, "A")
        node2 = FuzzNode(llm, "B")
        node3 = FuzzNode(llm, "C")
        node4 = FuzzNode(llm, "D")
        chain1 = FuzzChain([node1, node2])
        chain2 = FuzzChain([node3, node4])
        combined = chain1 | chain2
        assert len(combined) == 4

    def test_len(self):
        llm = MockLLMProvider()
        chain = FuzzChain(
            [
                FuzzNode(llm, "A"),
                FuzzNode(llm, "B"),
                FuzzNode(llm, "C"),
            ]
        )
        assert len(chain) == 3

    def test_repr(self):
        llm = MockLLMProvider()
        chain = FuzzChain([FuzzNode(llm, "Test")])
        repr_str = repr(chain)
        assert "FuzzChain" in repr_str
        assert "FuzzNode" in repr_str


class TestPipeOperatorChaining:
    @pytest.mark.asyncio
    async def test_triple_pipe_chain(self):
        llm = MockLLMProvider(["a", "b", "c"])
        node1 = FuzzNode(llm, "Step1: {input}")
        node2 = FuzzNode(llm, "Step2: {input}")
        node3 = FuzzNode(llm, "Step3: {input}")

        chain = node1 | node2 | node3
        result = await chain.run(input="start")

        assert result == "c"
        assert llm.prompts == snapshot(
            [
                "Step1: start",
                "Step2: a",
                "Step3: b",
            ]
        )

    @pytest.mark.asyncio
    async def test_chain_with_different_providers(self):
        llm1 = MockLLMProvider("from llm1")
        llm2 = MockLLMProvider("from llm2")

        node1 = FuzzNode(llm1, "Provider1: {input}")
        node2 = FuzzNode(llm2, "Provider2: {input}")

        chain = node1 | node2
        result = await chain.run(input="test")

        assert result == "from llm2"
        assert llm1.prompts == ["Provider1: test"]
        assert llm2.prompts == ["Provider2: from llm1"]


class TestProtocolCompliance:
    def test_llm_provider_protocol_mock(self):
        provider = MockLLMProvider()
        # Should have generate method that accepts prompt and kwargs
        assert hasattr(provider, "generate")

    def test_fuzz_node_has_run(self):
        llm = MockLLMProvider()
        node = FuzzNode(llm, "Test")
        assert hasattr(node, "run")

    def test_fuzz_chain_has_run(self):
        chain = FuzzChain()
        assert hasattr(chain, "run")
