from pydantic import BaseModel
from config.settings import DEFAULT_CUSTOM_AI

class ChatRequest(BaseModel):
    prompt: str
    model: str = "gemma3:4b-it-qat"
    chat_ai_id: int = None
    is_deep_think: bool = False
    is_search: bool = False
    is_deepsearch: bool = False

class ManagerChat(BaseModel):
    custom_ai: str = DEFAULT_CUSTOM_AI
