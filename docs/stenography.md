# Stenography Functions

The stenography module provides various text obfuscation and transformation techniques for security testing. This document explains its architecture and implementation.

## Overview

The module implements:

1. Rotation ciphers (ROT13, ROT5)
1. Base64 encoding
1. Text manipulation functions
1. Randomization techniques
1. Character substitution methods

## Core Functions

### Rotation Ciphers

```python
def rot13(input_text):
    """
    Applies ROT13 cipher to input text
    - Preserves case of letters
    - Leaves non-alphabetic characters unchanged
    """
    # Implementation details...

def rot5(input_text):
    """
    Applies ROT5 cipher to input text
    - Rotates digits by 5 positions
    - Leaves non-digit characters unchanged
    """
    # Implementation details...
```

### Encoding

```python
def base64_encode(data):
    """
    Encodes input data using Base64
    - Handles both string and bytes input
    - Returns UTF-8 encoded string
    """
    # Implementation details...
```

### Text Manipulation

```python
def mirror_words(text):
    """
    Reverses each word in the input text
    - Preserves word order
    - Maintains spaces between words
    """
    # Implementation details...

def scramble_words(text):
    """
    Randomly scrambles middle letters of words
    - Preserves first and last letters
    - Handles words shorter than 4 characters
    """
    # Implementation details...
```

### Randomization

```python
def randomize_letter_case(text):
    """
    Randomly changes case of each character
    - Independent case changes per character
    - Preserves non-letter characters
    """
    # Implementation details...

def insert_noise_characters(text, frequency=0.2):
    """
    Inserts random characters between existing ones
    - Configurable insertion frequency
    - Uses alphanumeric characters for noise
    """
    # Implementation details...
```

### Advanced Transformations

```python
def substitute_with_ascii(text):
    """
    Replaces characters with their ASCII codes
    - Space-separated numeric values
    - Preserves original character order
    """
    # Implementation details...

def remove_vowels(text):
    """
    Removes all vowel characters from text
    - Handles both lowercase and uppercase vowels
    - Preserves non-vowel characters
    """
    # Implementation details...

def zigzag_obfuscation(text):
    """
    Alternates character case in zigzag pattern
    - Starts with uppercase
    - Toggles case for each alphabetic character
    """
    # Implementation details...
```

## Usage Patterns

1. **Text Obfuscation**:

   ```python
   obfuscated = zigzag_obfuscation(
       scramble_words(
           insert_noise_characters(text)
       )
   )
   ```

1. **Encoding**:

   ```python
   encoded = base64_encode(rot13(text))
   ```

1. **Randomization**:

   ```python
   randomized = randomize_letter_case(
       remove_vowels(text)
   )
   ```

## Configuration

- **Noise Frequency**: Configurable in insert_noise_characters()
- **Scrambling**: Automatic handling of word lengths
- **Case Handling**: Preserved in rotation ciphers

## Limitations

- Primarily handles ASCII text
- Limited to implemented transformation types
- Randomization is not cryptographically secure
