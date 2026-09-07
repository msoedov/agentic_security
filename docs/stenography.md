# Stenography functions

`agentic_security.probe_data.stenography_fn` transforms prompts so scanners can
test whether a model still treats obfuscated text as an instruction.

The module is used by `Stenography` in `probe_data.data` when a dataset
enables encoding variants.

## Functions

| Function | What it does |
| --- | --- |
| `rot13` / `rot5` | Letter and digit rotation ciphers |
| `base64_encode` | Base64-encode a string or bytes |
| `mirror_words` | Reverse each word, keep word order |
| `scramble_words` | Shuffle middle letters, keep first and last |
| `randomize_letter_case` | Random per-character case |
| `insert_noise_characters` | Insert alphanumeric noise (`frequency=0.2` by default) |
| `substitute_with_ascii` | Replace characters with ordinals |
| `remove_vowels` | Drop `aeiou` in either case |
| `zigzag_obfuscation` | Alternate upper/lower case |
| `caesar_cipher` / `substitution_cipher` / `vigenere_cipher` | Classical ciphers |
| `code_block_encode` | Hide the prompt in a Python docstring fenced as code |

These are obfuscation helpers for red-team prompts, not cryptographic primitives.

## Usage

```python
from agentic_security.probe_data.stenography_fn import rot13, scramble_words

rot13("Ignore previous instructions")
scramble_words("Ignore previous instructions")
```
