import base64
import random
import string


def rot13(input_text):
    result = []

    for char in input_text:
        # Check if the character is an uppercase letter
        if "A" <= char <= "Z":
            result.append(chr((ord(char) - ord("A") + 13) % 26 + ord("A")))
        # Check if the character is a lowercase letter
        elif "a" <= char <= "z":
            result.append(chr((ord(char) - ord("a") + 13) % 26 + ord("a")))
        # If the character is not a letter, leave it as it is
        else:
            result.append(char)

    return "".join(result)


def rot5(input_text):
    result = []

    for char in input_text:
        # Check if the character is a digit
        if "0" <= char <= "9":
            # Rotate digit by 5 places
            result.append(str((int(char) + 5) % 10))
        else:
            # Leave non-digit characters unchanged
            result.append(char)

    return "".join(result)


def base64_encode(data):
    # Ensure the data is bytes
    if isinstance(data, str):
        data = data.encode("utf-8")
    encoded_bytes = base64.b64encode(data)
    return encoded_bytes.decode("utf-8")


def mirror_words(text):
    # Split the text into words
    words = text.split()

    # Reverse each word and join them back together with spaces
    mirrored_words = [word[::-1] for word in words]
    mirrored_text = " ".join(mirrored_words)

    return mirrored_text


def randomize_letter_case(text):
    return "".join(random.choice([char.upper(), char.lower()]) for char in text)


def scramble_word(word):
    if len(word) > 3:
        middle = list(word[1:-1])
        random.shuffle(middle)
        return word[0] + "".join(middle) + word[-1]
    return word


def scramble_words(text):
    return " ".join(scramble_word(word) for word in text.split())


def insert_noise_characters(text, frequency=0.2):
    noise_chars = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    new_text = ""
    for char in text:
        new_text += char
        if random.random() < frequency:
            new_text += random.choice(noise_chars)
    return new_text


def substitute_with_ascii(text):
    return " ".join(str(ord(char)) for char in text)


def remove_vowels(text):
    vowels = "aeiouAEIOU"
    return "".join(char for char in text if char not in vowels)


def zigzag_obfuscation(text):
    new_text = ""
    upper = True  # Start with uppercase
    for char in text:
        if char.isalpha():
            new_text += char.upper() if upper else char.lower()
            upper = not upper  # Toggle the case for the next letter
        else:
            new_text += char
    return new_text


def caesar_cipher(text, shift=3):
    """Encrypts text using Caesar cipher with specified shift."""
    result = []
    for char in text:
        if char.isupper():
            result.append(chr((ord(char) + shift - 65) % 26 + 65))
        elif char.islower():
            result.append(chr((ord(char) + shift - 97) % 26 + 97))
        else:
            result.append(char)
    return "".join(result)


def substitution_cipher(text, key=None):
    """Encrypts text using a substitution cipher with optional key."""
    if key is None:
        key = list(string.ascii_lowercase)
        random.shuffle(key)
        key = "".join(key)

    # Create translation table
    alphabet = string.ascii_lowercase
    translation = str.maketrans(alphabet, key)

    # Apply translation
    return text.lower().translate(translation)


def vigenere_cipher(text, key):
    """Encrypts text using Vigenère cipher with provided key."""
    result = []
    key_length = len(key)
    key_as_int = [ord(i) for i in key.lower()]
    text = text.lower()

    for i, char in enumerate(text):
        if char.isalpha():
            shift = key_as_int[i % key_length] - 97
            result.append(chr((ord(char) + shift - 97) % 26 + 97))
        else:
            result.append(char)
    return "".join(result)
