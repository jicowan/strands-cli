"""Custom tools for the TestSessionAgent agent."""

from typing import Callable, Dict, List

from strands import tool


@tool
def example_tool(input_text: str) -> str:
    """An example tool that the agent can use.

    Args:
        input_text: Input text to process.

    Returns:
        str: Processed output.
    """
    return f"Processed: {input_text}"


def register_tools() -> List[Callable]:
    """Register and return the tools available to the agent.

    Returns:
        List[Callable]: List of tool functions.
    """
    # Add your custom tools here
    return [
        example_tool,
    ]