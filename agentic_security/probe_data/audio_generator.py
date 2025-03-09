import base64
import logging
import os
import platform
import subprocess
import uuid

import httpx
from cache_to_disk import cache_to_disk

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AudioGenerationError(Exception):
    """Custom exception for errors during audio generation."""

    pass


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

    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error: {e}")
        raise AudioGenerationError("Failed to generate or convert audio.") from e
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise AudioGenerationError("Required file not found.") from e
    except Exception as e:
        logger.exception("Unexpected error occurred.")
        raise AudioGenerationError(
            "An unexpected error occurred during audio generation."
        ) from e
    finally:
        for path in (temp_aiff_path, temp_wav_path):
            try:
                if os.path.exists(path):
                    os.remove(path)
            except Exception as e:
                logger.warning(f"Failed to delete temporary file {path}: {e}")

    # Return the audio bytes
    return audio_bytes


def generate_audio_cross_platform(prompt: str) -> bytes:
    """
    Generate an audio file from the provided prompt using gTTS for cross-platform support.

    Parameters:
        prompt (str): Text to convert into audio.

    Returns:
        bytes: The audio data in MP3 format.
    """
    from gtts import gTTS  # Import gTTS for cross-platform support

    tts = gTTS(text=prompt, lang="en")
    temp_mp3_path = f"temp_audio_{uuid.uuid4().hex}.mp3"
    tts.save(temp_mp3_path)

    try:
        with open(temp_mp3_path, "rb") as f:
            audio_bytes = f.read()
    finally:
        if os.path.exists(temp_mp3_path):
            os.remove(temp_mp3_path)

    return audio_bytes


@cache_to_disk()
def generate_audioform(prompt: str) -> bytes:
    """
    Generate an audio file from the provided prompt in WAV format.
    Uses macOS 'say' command if the operating system is macOS, otherwise uses gTTS.

    Parameters:
        prompt (str): Text to convert into audio.

    Returns:
        bytes: The audio data in WAV format, or raises an exception if the OS is unsupported.
    """
    current_os = platform.system()
    if current_os == "Darwin":  # macOS
        return generate_audio_mac_wav(prompt)
    elif current_os in ["Windows", "Linux"]:
        return generate_audio_cross_platform(prompt)
    else:
        raise NotImplementedError(
            "Audio generation is only supported on macOS, Windows, and Linux for now."
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
