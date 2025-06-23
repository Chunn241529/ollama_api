from typing import List, Dict, Optional
from pydantic import BaseModel
from config.settings import DEFAULT_CUSTOM_AI

class ChatRequest(BaseModel):
    prompt: str
    model: str = "gemma3:4b-it-qat"
    chat_ai_id: int = None
    is_deep_think: bool = False
    is_search: bool = False
    is_deepsearch: bool = False
    is_image: bool = False
    messages: Optional[List[Dict]] = None  # Thêm trường messages kiểu List[Dict] với giá trị mặc định None

class ManagerChat(BaseModel):
    custom_ai: str = DEFAULT_CUSTOM_AI

class SavePartialRequest(BaseModel):
    content: str
    chat_ai_id: Optional[int] = None
    is_thinking: bool = False
