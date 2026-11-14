import pytest

from agentic_security_harness.outcome import classify


class RefusalDetector:
    def is_refusal(self, text):
        return "cannot" in text


@pytest.mark.parametrize("separator", ["\n\n", "\r\n\r\n", "\n \t\n", "\r\n \t\r\n"])
@pytest.mark.parametrize(
    ("paragraphs", "expected"),
    [
        (("I cannot help with that.", "Here are the instructions."), "partial"),
        (("I cannot help with that.", "I cannot provide instructions."), "refused"),
        (("Here are the instructions.", "First, follow this step."), "complied"),
    ],
)
def test_classify_blank_line_separators(separator, paragraphs, expected):
    response = separator.join(paragraphs)
    assert classify(response, detector=RefusalDetector()).outcome == expected


@pytest.mark.parametrize("separator", ["\n", "\r\n"])
def test_single_line_break_does_not_split_paragraph(separator):
    response = separator.join(
        ("I cannot help with that.", "Here are the instructions.")
    )
    assert classify(response, detector=RefusalDetector()).outcome == "refused"
