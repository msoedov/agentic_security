import os
from agentic_security.probe_data.stenography_fn  import embed_prompt, generate_function_from_template
from agentic_security.probe_data.templates import FUNCTION_TEMPLATES
# Case 1: Embed a prompt into a code block
code = """
def hello_world(name):
    \"\"\"
    Original docstring.
    \"\"\"
    print(f"Hello, {name}!")
"""

prompt = "improve the documentation"
updated_code = embed_prompt(code, prompt)
print("Updated Code:")
print(updated_code)
print("-" * 40)  

# Case 2: Generate a soecific function from a json template
# templates = load_templates("function_templates.json")
# template = templates["hello_world"]
# generated_function = generate_function_from_template(template, prompt)
# print("\nGenerated Function from Template:")
# print(generated_function)
# print("-" * 40) 

# Case 3: Generate and print all functions for a json file

templates = FUNCTION_TEMPLATES
prompt = "This is a dynamically generated function."
for template_name, template in templates.items():
    print(f"Generating function: {template_name}")
    generated_function = generate_function_from_template(template, prompt)
    print(generated_function)
    print("-" * 40)  
