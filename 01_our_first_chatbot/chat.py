"""
Instructions:
- Implement the `chat` function below.
- The function should take a message and a history of messages.
- The function should return a string (stream=False) or an iterator of strings (stream=True).
- The function should use the an LLM to generate a response.
- Test your function with the following code: python -m 01_our_first_chatbot. The gradio interface is handled in the `__main__.py` file.
"""

from .constants import GEMINI_MODEL
from .prompts import SYSTEM_PROMPT
from litellm import completion
from typing import Iterator

def chat(message:str, history:list[dict]) -> Iterator[str] | str:
    """
    Chat with the Gemini model.

    Args:
        message (str): The message to chat with.
        history (list): The history of the chat.

    Returns:
        Iterator[str] | str: The response from the model.
    """
    raise NotImplementedError("Not implemented")