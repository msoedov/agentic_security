# templates.py
FUNCTION_TEMPLATES = {
    "hello_world": {
        "name": "hello_world",
        "params": ["name"],
        "docstring": "{PROMPT}",
        "body": "print(f'Hello, {name}!')"
    },
    "add_numbers": {
        "name": "add_numbers",
        "params": ["a", "b"],
        "docstring": "{PROMPT}",
        "body": "return a + b"
    },
    "multiply_numbers": {
        "name": "multiply_numbers",
        "params": ["x", "y"],
        "docstring": "{PROMPT}",
        "body": "return x * y"
    }
}