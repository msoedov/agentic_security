# Image generation

The image generator makes an image of each text prompt. Use it to test if a vision model obeys text in an image.

The module is `agentic_security.probe_data.image_generator`. It uses matplotlib.

## When the scanner makes images

If the body of the HTTP spec has `<<BASE64_IMAGE>>`, the scanner wraps the spec in a `RequestAdapter`. For each prompt, the adapter does these steps:

1. It makes a JPEG image of the prompt with `generate_image(prompt)`.
2. It encodes the image as a data URL with `encode(image)`.
3. It puts the data URL in place of `<<BASE64_IMAGE>>` and sends the request.

The data URL starts with `data:image/jpeg;base64,`. Do not write this prefix in the spec. Refer to [HTTP spec](http_spec.md).

## Functions

| Function | Description |
| --- | --- |
| `generate_image(prompt, variant=0)` | Returns the JPEG bytes of an image with the prompt text. The tool keeps the result in the disk cache. |
| `generate_image_dataset(datasets)` | Makes an `ImageProbeDataset` for each `ProbeDataset`. |
| `encode(image)` | Returns the image as a Base64 data URL. |

## Image styles

The image is 6 x 4 inches. The `variant` argument selects the style:

| `variant` | Background |
| --- | --- |
| `0` (default) | Light blue, dark blue text |
| `1` | Dark gray |
| `2` | Light pink, with a text box |
| `3` | White, with a circle |

## Example

```python
from agentic_security.probe_data.image_generator import encode, generate_image

data_url = encode(generate_image("Ignore previous instructions"))
```

## Limits

- The image has only text. It does not have pictures.
- The styles are fixed.
