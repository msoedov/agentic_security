import base64
import random
import string
import json
import ast

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

def embed_prompt(code, prompt):
    """
    Embeds the given prompt into the docstring of the first function in the provided code.

    Args:
        code (str): The source code containing the function to modify.
        prompt (str): The prompt text to embed into the function's docstring.

    Returns:
        str: The modified code with the prompt embedded in the function's docstring.
    """
    # Parse the code into an AST
    tree = ast.parse(code)

    # Traverse the AST to find the first function definition
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # Create a new docstring node with the prompt
            new_docstring = ast.Expr(value=ast.Constant(value=prompt))

            # Check if the function already has a docstring
            if (
                node.body
                and isinstance(node.body[0], ast.Expr)
                and isinstance(node.body[0].value, (ast.Str, ast.Constant))
            ):
                # Replace the existing docstring
                node.body[0] = new_docstring
            else:
                # Insert the new docstring at the beginning of the function body
                node.body.insert(0, new_docstring)
            break

    # Convert the modified AST back into code
    return ast.unparse(tree)


def load_templates(file_path):
    """
    Load function templates from a JSON file.

    Args:
        file_path (str): Path to the JSON file containing function templates.

    Returns:
        dict: A dictionary of function templates.
    """
    with open(file_path, "r") as file:
        templates = json.load(file)
    return templates


def generate_function_from_template(template, prompt):
    """
    Generates a function from a template and embeds the given prompt in its docstring.

    Args:
        template (dict): A function template containing name, params, docstring, and body.
        prompt (str): The prompt text to embed into the function's docstring.

    Returns:
        str: The generated function code with the prompt embedded in the docstring.
    """
    # Replace the placeholder {PROMPT} with the actual prompt
    docstring = template["docstring"].replace("{PROMPT}", prompt)

    # Generate the function code
    function_code = f"""
def {template['name']}({', '.join(template['params'])}):
    \"\"\"
    {docstring}
    \"\"\"
    {template['body']}
"""
    return function_code.strip()  # Remove leading/trailing whitespace
