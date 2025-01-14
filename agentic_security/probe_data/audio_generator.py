import base64
import os
import platform
import subprocess
import uuid

import httpx
from cache_to_disk import cache_to_disk


def encode(content: bytes) -> str:
    encoded_content = base64.b64encode(content).decode("utf-8")
    return "data:audio/mpeg;base64," + encoded_content


def generate_audio_mac_wav(prompt: str) -> bytes:
    """
    Generate an audio file from the provided prompt using macOS 'say' command
    and return it as bytes in WAV format.

    Parameters:
        prompt (str): Text to convert into audio.

    Returns:
        bytes: The audio data in WAV format.
    """
    # Generate unique temporary file paths
    temp_aiff_path = f"temp_audio_{uuid.uuid4().hex}.aiff"
    temp_wav_path = f"temp_audio_{uuid.uuid4().hex}.wav"

    try:
        # Use the 'say' command to generate AIFF audio
        subprocess.run(["say", "-o", temp_aiff_path, prompt], check=True)

        # Convert AIFF to WAV using afconvert
        subprocess.run(
            ["afconvert", "-f", "WAVE", "-d", "LEI16", temp_aiff_path, temp_wav_path],
            check=True,
        )

        # Read the WAV file into memory
        with open(temp_wav_path, "rb") as f:
            audio_bytes = f.read()
    finally:
        # Clean up the temporary files
        if os.path.exists(temp_aiff_path):
            os.remove(temp_aiff_path)
        if os.path.exists(temp_wav_path):
            os.remove(temp_wav_path)

    # Return the audio bytes
    return audio_bytes


@cache_to_disk()
def generate_audioform(prompt: str) -> bytes:
    """
    Generate an audio file from the provided prompt in WAV format.
    Uses macOS 'say' command if the operating system is macOS.

    Parameters:
        prompt (str): Text to convert into audio.

    Returns:
        bytes: The audio data in WAV format, or raises an exception if the OS is unsupported.
    """
    current_os = platform.system()
    if current_os == "Darwin":  # macOS
        return generate_audio_mac_wav(prompt)
    else:
        raise NotImplementedError(
            "Audio generation is only supported on macOS for now."
        )


class RequestAdapter:
    # Adapter of http_spec.LLMSpec

    def __init__(self, llm_spec):
        self.llm_spec = llm_spec
        if not llm_spec.has_audio:
            raise ValueError("LLMSpec must have an image")

    async def probe(
        self, prompt: str, encoded_image: str = "", encoded_audio: str = "", files={}
    ) -> httpx.Response:
        encoded_audio = generate_audioform(prompt)
        encoded_audio = encode(encoded_audio)
        return await self.llm_spec.probe(prompt, encoded_image, encoded_audio, files)

    fn = probe
