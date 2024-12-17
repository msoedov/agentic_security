SAMPLE_SPEC = """
POST http://0.0.0.0:9094/v1/self-probe
Authorization: Bearer XXXXX
Content-Type: application/json

{
    "prompt": "<<PROMPT>>"
}
"""


IMAGE_SPEC = """
POST http://0.0.0.0:9094/v1/self-probe-image
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
"""


MULTI_IMAGE_SPEC = """
POST http://0.0.0.0:9094/v1/self-probe-image
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
        {
          "type": "image_url",
          "image_url": {
            "url":  f"data:image/jpeg;base64,{<<BASE64_IMAGE>>}"
          },
        },
      ],
    }
]
"""


FILE_SPEC = """
POST http://0.0.0.0:9094/v1/self-probe-file
Authorization: Bearer $GROQ_API_KEY
Content-Type: multipart/form-data

{
  "file": "@./sample_audio.m4a",
  "model": "whisper-large-v3"
}
"""

ALL = [SAMPLE_SPEC, IMAGE_SPEC, MULTI_IMAGE_SPEC, FILE_SPEC]
