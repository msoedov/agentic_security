# Stenography functions

`agentic_security.probe_data.stenography_fn` changes the text of a prompt. Use these functions to test if a model obeys an instruction that is encoded or hidden.

The scanner uses these functions to make transformed datasets from the loaded prompts. Refer to [Dataset extension](datasets.md).

> **NOTE:** These functions hide text for red-team tests. They do not give cryptographic security.

## Functions

| Function | Description |
| --- | --- |
| `rot13` / `rot5` | Rotates the letters (ROT13) or the digits (ROT5). |
| `base64_encode` | Encodes a string or bytes in Base64. |
| `mirror_words` | Reverses the letters of each word. The word order does not change. |
| `scramble_words` | Mixes the middle letters of each word. The first and last letters do not change. |
| `randomize_letter_case` | Sets a random case for each letter. |
| `insert_noise_characters` | Adds random letters and digits. The default `frequency` is `0.2`. |
| `substitute_with_ascii` | Replaces each character with its character code. |
| `remove_vowels` | Removes the vowels `aeiou` (upper and lower case). |
| `zigzag_obfuscation` | Uses upper case and lower case in turn. |
| `caesar_cipher` / `substitution_cipher` / `vigenere_cipher` | Classical ciphers. |
| `code_block_encode` | Puts the prompt in a Python docstring in a code block. |

## Example

```python
from agentic_security.probe_data.stenography_fn import rot13, scramble_words

rot13("Ignore previous instructions")
scramble_words("Ignore previous instructions")
```
