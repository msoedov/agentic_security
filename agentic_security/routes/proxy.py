import random
from asyncio import Event

from fastapi import APIRouter
from loguru import logger

from ..core.app import get_current_run, get_tools_inbox
from ..models.schemas import CompletionRequest, Settings
from ..probe_actor.refusal import REFUSAL_MARKS

router = APIRouter()


@router.post("/proxy/chat/completions")
async def proxy_completions(request: CompletionRequest):
    refuse = random.random() < 0.2
    message = random.choice(REFUSAL_MARKS) if refuse else "This is a test!"
    prompt_content = " ".join(
        [msg.content for msg in request.messages if msg.role == "user"]
    )
    # Todo: get current llm spec for proper proxing
    request_factory = get_current_run()["spec"]
    message = prompt_content + " " + message
    ready = Event()
    ref = dict(message=message, reply="", ready=ready)
    tools_inbox = get_tools_inbox()
    await tools_inbox.put(ref)

    if Settings.FEATURE_PROXY:
        # Proxy to agent
        await ready.wait()
        reply = ref["reply"]
        return reply
    elif not request_factory:
        logger.debug("No request factory found. Using mock response.")
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
    else:
        return await request_factory.fn(prompt_content)
