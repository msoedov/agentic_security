_SPECS = [
    """POST ${SELF_URL}/v1/self-probe
Authorization: Bearer XXXXX
Content-Type: application/json

{
"prompt": "<<PROMPT>>"
}

""",
    """POST https://api.openai.com/v1/chat/completions
Authorization: Bearer $OPENAI_API_KEY
Content-Type: application/json

{
"model": "gpt-3.5-turbo",
"messages": [{"role": "user", "content": "<<PROMPT>>"}],
"temperature": 0.7
}
""",
    """
POST https://api.deepseek.com/chat/completions
Authorization: Bearer $DEEPSEEK_API_KEY
Content-Type: application/json

{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "<<PROMPT>>"}
  ],
  "stream": false
}
""",
    """POST https://api.replicate.com/v1/models/mistralai/mixtral-8x7b-instruct-v0.1/predictions
Authorization: Bearer $APIKEY
Content-Type: application/json

{
"input": {
"top_k": 50,
"top_p": 0.9,
"prompt": "Write a bedtime story about neural networks I can read to my toddler",
"temperature": 0.6,
"max_new_tokens": 1024,
"prompt_template": "<s>[INST] <<PROMPT>> [/INST] ",
"presence_penalty": 0,
"frequency_penalty": 0
}
}
""",
    """POST https://api.groq.com/v1/request_manager/text_completion
Authorization: Bearer $APIKEY
Content-Type: application/json

{
"model_id": "codellama-34b",
"system_prompt": "You are helpful and concise coding assistant",
"user_prompt": "<<PROMPT>>"
}
""",
    """POST https://api.together.xyz/v1/chat/completions
Authorization: Bearer $TOGETHER_API_KEY
Content-Type: application/json

{
"model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
"messages": [
{"role": "system", "content": "You are an expert travel guide"},
{"role": "user", "content": "<<PROMPT>>"}
]
}
""",
    """POST ${SELF_URL}/v1/self-probe-image
Authorization: Bearer XXXXX
Content-Type: application/json

[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this image?",
        },
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{<<BASE64_IMAGE>>}"
          },
        },
      ],
    }
]
""",
    """POST ${SELF_URL}/v1/self-probe-file
Authorization: Bearer $API_KEY
Content-Type: multipart/form-data

{
  "file": "@./sample_audio.m4a",
  "model": "whisper-large-v3"
}
""",
    """POST https://api.gemini.com/v1/generate
Authorization: Bearer $GEMINI_API_KEY
Content-Type: application/json

{
  "model": "gemini-latest",
  "prompt": "<<PROMPT>>",
  "temperature": 0.8,
  "max_tokens": 150,
  "top_p": 1.0,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
""",
    """POST https://api.anthropic.com/v1/complete
Authorization: Bearer $ANTHROPIC_API_KEY
Content-Type: application/json

{
  "model": "claude-v1.3",
  "prompt": "<<PROMPT>>",
  "temperature": 0.7,
  "max_tokens_to_sample": 256,
  "stop_sequences": ["\n\nHuman:"]
}
""",
    """POST https://api.cohere.ai/generate
Authorization: Bearer $COHERE_API_KEY
Content-Type: application/json

{
  "model": "command-xlarge-nightly",
  "prompt": "<<PROMPT>>",
  "max_tokens": 300,
  "temperature": 0.75,
  "k": 0,
  "p": 0.75
}
""",
    """POST https://<<RESOURCE_NAME>>.openai.azure.com/openai/deployments/<<DEPLOYMENT_NAME>>/completions?api-version=2023-06-01-preview
Authorization: Bearer $AZURE_API_KEY
Content-Type: application/json

{
  "prompt": "<<PROMPT>>",
  "max_tokens": 150,
  "temperature": 0.7,
  "top_p": 0.9,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
""",
    """POST https://api.assemblyai.com/v2/transcript
Authorization: Bearer $ASSEMBLY_API_KEY
Content-Type: application/json

{
  "audio_url": "<<AUDIO_FILE_URL>>"
}
""",
    """POST https://api.openrouter.ai/v1/chat/completions
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json

{
  "model": "openrouter-latest",
  "prompt": "<<PROMPT>>",
  "temperature": 0.7,
  "max_tokens": 150,
  "top_p": 0.9,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
""",
]


LLM_SPECS = [
    """POST ${SELF_URL}/v1/self-probe
Authorization: Bearer XXXXX
Content-Type: application/json

{
"prompt": "<<PROMPT>>"
}

""",
    """POST https://api.openai.com/v1/chat/completions
Authorization: Bearer $OPENAI_API_KEY
Content-Type: application/json

{
"model": "gpt-3.5-turbo",
"messages": [{"role": "user", "content": "<<PROMPT>>"}],
"temperature": 0.7
}
""",
    """
POST https://api.deepseek.com/chat/completions
Authorization: Bearer $DEEPSEEK_API_KEY
Content-Type: application/json

{
  "model": "deepseek-chat",
  "messages": [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "<<PROMPT>>"}
  ],
  "stream": false
}
""",
    """POST https://api.replicate.com/v1/models/mistralai/mixtral-8x7b-instruct-v0.1/predictions
Authorization: Bearer $APIKEY
Content-Type: application/json

{
"input": {
"top_k": 50,
"top_p": 0.9,
"prompt": "Write a bedtime story about neural networks I can read to my toddler",
"temperature": 0.6,
"max_new_tokens": 1024,
"prompt_template": "<s>[INST] <<PROMPT>> [/INST] ",
"presence_penalty": 0,
"frequency_penalty": 0
}
}
""",
    """POST https://api.groq.com/v1/request_manager/text_completion
Authorization: Bearer $APIKEY
Content-Type: application/json

{
"model_id": "codellama-34b",
"system_prompt": "You are helpful and concise coding assistant",
"user_prompt": "<<PROMPT>>"
}
""",
    """POST https://api.together.xyz/v1/chat/completions
Authorization: Bearer $TOGETHER_API_KEY
Content-Type: application/json

{
"model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
"messages": [
{"role": "system", "content": "You are an expert travel guide"},
{"role": "user", "content": "<<PROMPT>>"}
]
}
""",
    """POST ${SELF_URL}/v1/self-probe-image
Authorization: Bearer XXXXX
Content-Type: application/json

[
    {
      "role": "user",
      "content": [
        {
          "type": "text",
          "text": "What is in this image?",
        },
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{<<BASE64_IMAGE>>}"
          },
        },
      ],
    }
]
""",
    """POST ${SELF_URL}/v1/self-probe-file
Authorization: Bearer $API_KEY
Content-Type: multipart/form-data

{
  "file": "@./sample_audio.m4a",
  "model": "whisper-large-v3"
}
""",
    """POST https://api.gemini.com/v1/generate
Authorization: Bearer $GEMINI_API_KEY
Content-Type: application/json

{
  "model": "gemini-latest",
  "prompt": "<<PROMPT>>",
  "temperature": 0.8,
  "max_tokens": 150,
  "top_p": 1.0,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
""",
    """POST https://api.anthropic.com/v1/complete
Authorization: Bearer $ANTHROPIC_API_KEY
Content-Type: application/json

{
  "model": "claude-v1.3",
  "prompt": "<<PROMPT>>",
  "temperature": 0.7,
  "max_tokens_to_sample": 256,
  "stop_sequences": ["\n\nHuman:"]
}
""",
    """POST https://api.cohere.ai/generate
Authorization: Bearer $COHERE_API_KEY
Content-Type: application/json

{
  "model": "command-xlarge-nightly",
  "prompt": "<<PROMPT>>",
  "max_tokens": 300,
  "temperature": 0.75,
  "k": 0,
  "p": 0.75
}
""",
    """POST https://<<RESOURCE_NAME>>.openai.azure.com/openai/deployments/<<DEPLOYMENT_NAME>>/completions?api-version=2023-06-01-preview
Authorization: Bearer $AZURE_API_KEY
Content-Type: application/json

{
  "prompt": "<<PROMPT>>",
  "max_tokens": 150,
  "temperature": 0.7,
  "top_p": 0.9,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
""",
    """POST https://api.assemblyai.com/v2/transcript
Authorization: Bearer $ASSEMBLY_API_KEY
Content-Type: application/json

{
  "audio_url": "<<AUDIO_FILE_URL>>"
}
""",
    """POST https://api.openrouter.ai/v1/chat/completions
Authorization: Bearer $OPENROUTER_API_KEY
Content-Type: application/json

{
  "model": "openrouter-latest",
  "prompt": "<<PROMPT>>",
  "temperature": 0.7,
  "max_tokens": 150,
  "top_p": 0.9,
  "frequency_penalty": 0,
  "presence_penalty": 0
}
""",
]


LLM_CONFIGS = [
    {
        "name": "Custom API",
        "prompts": 40000,
        "customInstructions": "Requires api spec",
        "logo": "/icons/myshell.png",
    },
    {"name": "Open AI", "prompts": 24000, "logo": "/icons/openai.png"},
    {"name": "Deepseek v1", "prompts": 24000, "logo": "/icons/deepseek.png"},
    {"name": "Replicate", "prompts": 40000, "logo": "/icons/replicate.png"},
    {"name": "Groq", "prompts": 40000, "logo": "/icons/groq.png"},
    {"name": "Together.ai", "prompts": 40000, "logo": "/icons/together.png"},
    {
        "name": "Custom API Image",
        "prompts": 40000,
        "customInstructions": "Requires api spec",
        "modality": "Image",
        "logo": "/icons/myshell.png",
    },
    {
        "name": "Custom API Files",
        "prompts": 40000,
        "customInstructions": "Requires api spec",
        "modality": "Files",
        "logo": "/icons/myshell.png",
    },
    {"name": "Gemini", "prompts": 40000, "logo": "/icons/gemini.png"},
    {"name": "Claude", "prompts": 40000, "logo": "/icons/claude.png"},
    {"name": "Cohere", "prompts": 40000, "logo": "/icons/cohere.png"},
    {"name": "Azure OpenAI", "prompts": 40000, "logo": "/icons/azureai.png"},
    {"name": "assemblyai", "prompts": 40000, "logo": "/icons/myshell.png"},
    {"name": "OpenRouter.ai", "prompts": 40000, "logo": "/icons/openrouter.png"},
]

LLM_SPECS = [dict(spec=spec, **d) for spec, d in zip(_SPECS, LLM_CONFIGS)]
