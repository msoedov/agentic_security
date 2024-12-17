import random

from fastapi import APIRouter, File, Header, HTTPException, UploadFile

from ..models.schemas import FileProbeResponse, Probe
from ..probe_actor.refusal import REFUSAL_MARKS
from ..probe_data import REGISTRY

router = APIRouter()


@router.post("/v1/self-probe")
def self_probe(probe: Probe):
    refuse = random.random() < 0.2
    message = random.choice(REFUSAL_MARKS) if refuse else "This is a test!"
    message = probe.prompt + " " + message
    return {
        "id": "chatcmpl-abc123",
        "object": "chat.completion",
        "created": 1677858242,
        "model": "gpt-3.5-turbo-0613",
        "usage": {"prompt_tokens": 13, "completion_tokens": 7, "total_tokens": 20},
        "choices": [
            {
                "message": {"role": "assistant", "content": message},
                "logprobs": None,
                "finish_reason": "stop",
                "index": 0,
            }
        ],
    }


@router.post("/v1/self-probe-file", response_model=FileProbeResponse)
async def self_probe_file(
    file: UploadFile = File(...),
    model: str = "whisper-large-v3",
    authorization: str = Header(...),
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    api_key = authorization.replace("Bearer ", "")
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    if not file.filename or not file.filename.lower().endswith(
        (".m4a", ".mp3", ".wav")
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Supported formats: m4a, mp3, wav",
        )

    # For testing purposes, return mock transcription
    mock_text = "This is a mock transcription of the audio file."

    return FileProbeResponse(text=mock_text, model=model)


@router.get("/v1/data-config")
async def data_config():
    return [m for m in REGISTRY]
