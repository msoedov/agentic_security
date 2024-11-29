import random
from fastapi import APIRouter
from ..models.schemas import Probe
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


@router.get("/v1/data-config")
async def data_config():
    return [m for m in REGISTRY]
