from claude_client import send_claude_prompt

def example_usage():
    """Example of how to use the Claude client utility"""

    # Example 1: Basic usage
    system_prompt = "You are a helpful assistant that provides clear, concise answers."
    instruction_prompt = "Explain what a web crawler is in simple terms."

    response = send_claude_prompt(
        system_prompt=system_prompt,
        instruction_prompt=instruction_prompt
    )

    print("Basic response:")
    print(response)
    print("-" * 50)

    # Example 2: With output structure
    system_prompt = "You are a technical documentation assistant."
    instruction_prompt = "Explain the key components of a web crawler system."
    output_structure_prompt = """Please format your response as JSON with the following structure:
    {
        "components": [
            {
                "name": "component_name",
                "description": "brief description",
                "importance": "high/medium/low"
            }
        ]
    }"""

    response = send_claude_prompt(
        system_prompt=system_prompt,
        instruction_prompt=instruction_prompt,
        output_structure_prompt=output_structure_prompt
    )

    print("Structured response:")
    print(response)
    print("-" * 50)

    # Example 3: Code generation
    system_prompt = "You are a Python programming expert."
    instruction_prompt = "Write a function that validates if a URL is properly formatted."
    output_structure_prompt = "Please provide only the Python function code with docstring."

    response = send_claude_prompt(
        system_prompt=system_prompt,
        instruction_prompt=instruction_prompt,
        output_structure_prompt=output_structure_prompt,
        max_tokens=1000
    )

    print("Code generation response:")
    print(response)

if __name__ == "__main__":
    try:
        example_usage()
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure you have set CLAUDE_API_KEY in your .env file")