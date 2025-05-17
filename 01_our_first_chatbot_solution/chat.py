from .constants import GEMINI_MODEL
from .prompts import SYSTEM_PROMPT
from litellm import completion
from typing import Iterator

def chat(message:str, history:list[dict]) -> Iterator[str]:
    """
    Chat with the Gemini model.

    Args:
        message (str): The message to chat with.
        history (list): The history of the chat.

    Returns:
        Iterator[str]: The response from the model.
    """
    # If the history is empty, add the system prompt
    if not len(history):
        history.append({'role': 'system', 'content': SYSTEM_PROMPT})
    # Add the user's message to the history
    history.append({'role': 'user', 'content': message})
    # Get the response from the model
    response = completion(model=GEMINI_MODEL, messages=history, stream=True)
    # Stream the response
    to_return = ""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            to_return += chunk.choices[0].delta.content
            yield to_return