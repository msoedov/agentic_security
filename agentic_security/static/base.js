
let URL = window.location.href;
if (URL.endsWith('/')) {
    URL = URL.slice(0, -1);
}
URL = URL.replace('/#', '');

// Vue application
let LLM_SPECS = [
    `POST ${URL}/v1/self-probe
Authorization: Bearer XXXXX
Content-Type: application/json

{
"prompt": "<<PROMPT>>"
}

`,
    `POST https://api.openai.com/v1/chat/completions
Authorization: Bearer sk-xxxxxxxxx
Content-Type: application/json

{
"model": "gpt-3.5-turbo",
"messages": [{"role": "user", "content": "<<PROMPT>>"}],
"temperature": 0.7
}
`,
    `POST https://api.replicate.com/v1/models/mistralai/mixtral-8x7b-instruct-v0.1/predictions
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
`,
    `POST https://api.groq.com/v1/request_manager/text_completion
Authorization: Bearer $APIKEY
Content-Type: application/json

{
"model_id": "codellama-34b",
"system_prompt": "You are helpful and concise coding assistant",
"user_prompt": "<<PROMPT>>"
}
`,
    `POST https://api.together.xyz/v1/chat/completions
Authorization: Bearer $TOGETHER_API_KEY
Content-Type: application/json

{
"model": "mistralai/Mixtral-8x7B-Instruct-v0.1",
"messages": [
{"role": "system", "content": "You are an expert travel guide"},
{"role": "user", "content": "<<PROMPT>>"}
]
}
`,
]
