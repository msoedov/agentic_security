
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
  `POST ${URL}/v1/self-probe-image
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
`,
  `POST ${URL}/v1/self-probe-file
Authorization: Bearer $GROQ_API_KEY
Content-Type: multipart/form-data

{
  "file": "@./sample_audio.m4a",
  "model": "whisper-large-v3"
}
`,
]


let LLM_CONFIGS = [
  { name: 'Custom API', prompts: 40000, customInstructions: 'Requires api spec' },
  { name: 'Open AI', prompts: 24000 },
  { name: 'Replicate', prompts: 40000 },
  { name: 'Groq', prompts: 40000 },
  { name: 'Together.ai', prompts: 40000 },
  { name: 'Custom API Image', prompts: 40000, customInstructions: 'Requires api spec' },
  { name: 'Custom API Files', prompts: 40000, customInstructions: 'Requires api spec' },

]

function has_image(spec) {
  return spec.includes('<<BASE64_IMAGE>>');
}

function has_files(spec) {
  return spec.includes('multipart/form-data');
}


function _getFailureRateColor(failureRate) {
  // We're now working with the strength percentage, so no need to invert
  const strengthRate = 100 - failureRate;

  if (strengthRate >= 95) return 'text-green-400';
  else if (strengthRate >= 85) return 'text-green-400';
  else if (strengthRate >= 75) return 'text-green-500';
  else if (strengthRate >= 65) return 'text-yellow-400';
  else if (strengthRate >= 55) return 'text-yellow-500';
  else if (strengthRate >= 45) return 'text-orange-400';
  else if (strengthRate >= 35) return 'text-orange-500';
  else if (strengthRate >= 25) return 'text-dark-accent-red';
  else if (strengthRate >= 15) return 'text-red-400';
  else if (strengthRate > 0) return 'text-red-500';
  else return 'text-gray-100'; // This can be the default for strengthRate of 0 or less
}

function _getFailureRateScore(failureRate) {
  // Convert failureRate to a strength percentage
  const strengthRate = 100 - failureRate;

  if (strengthRate >= 90) return 'A';
  else if (strengthRate >= 80) return 'B';
  else if (strengthRate >= 70) return 'C';
  else if (strengthRate >= 60) return 'D';
  else return 'E'; // For strengthRate less than 60
}
