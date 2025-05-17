import gradio as gr
from ctme.utils import get_root_dotenv
from .chat import chat

_ = get_root_dotenv(load=True)

if __name__ == "__main__":
    gr.ChatInterface(chat).launch()