import platform

import pytest

from agentic_security.probe_data.audio_generator import (
    generate_audio_cross_platform,
    generate_audio_mac_wav,
    generate_audioform,
)


def test_generate_audio_mac_wav():
    if platform.system() == "Darwin":
        prompt = "Hello, this is a test."
        audio_bytes = generate_audio_mac_wav(prompt)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
    else:
        pytest.skip("Test is only applicable on macOS.")


def test_generate_audioform_mac():
    if platform.system() == "Darwin":
        prompt = "Testing audio generation."
        audio_bytes = generate_audioform(prompt)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0


def test_generate_audio_cross_platform():
    if platform.system() in ["Windows", "Linux"]:
        prompt = "This is a cross-platform test."
        audio_bytes = generate_audio_cross_platform(prompt)
        assert isinstance(audio_bytes, bytes)
        assert len(audio_bytes) > 0
    else:
        pytest.skip("Test is only applicable on Windows and Linux.")
