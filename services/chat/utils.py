from functools import lru_cache
from typing import Dict, Any

@lru_cache(maxsize=1000)
def prepare_options(model: str, temperature: float, max_tokens: int, top_p: float) -> Dict[str, Any]:
    """Prepare and cache the API options."""
    return {
        "temperature": temperature,
        "num_predict": max_tokens,
        "top_p": top_p,
        "repeat_penalty": 1.2,
    }

def prepare_payload(model: str, messages: list, temperature: float, max_tokens: int, top_p: float) -> Dict[str, Any]:
    """Prepare the API payload."""
    return {
        "model": model,
        "messages": messages,
        "options": prepare_options(model, temperature, max_tokens, top_p),
        "stream": True,
    }

@lru_cache(maxsize=100)
def get_task_handler(task_type: str) -> str:
    """Cache and return task handler templates."""
    task_handlers = {
        "analys_question": lambda messages: f"""
            Xét câu hỏi: '{messages}'.
            - Nếu câu hỏi không đủ rõ, vô lý, hoặc không thể suy luận (ví dụ: "Mùi của mưa nặng bao nhiêu?"), trả về: "Khó nha bro, [lý do ngắn gọn tự nhiên]."
            - Nếu câu hỏi có thể suy luận được:
                1. Tạo keyword: Lấy 2-4 từ khóa chính từ câu hỏi (ngắn gọn, sát nghĩa).
                2. Phân tích từng keyword: Mỗi từ khóa gợi lên ý gì? Liên quan thế nào đến ý định người dùng?
                3. Tổng hợp:
                    * Ý định: Người dùng muốn gì? (thông tin, giải pháp, hay gì khác)
                    * Cách hiểu: Câu hỏi có thể diễn giải thế nào?
            Reasoning và viết ngắn gọn, tự nhiên.
        """,
        "better_question": lambda messages: f"""
            Câu hỏi gốc: '{messages}'
            Xét kỹ câu hỏi này: Nó thiếu gì để rõ nghĩa hơn? Bổ sung sao cho tự nhiên, cụ thể và dễ hiểu, như cách nói chuyện với bạn. Viết lại thành câu hỏi đầy đủ, giữ ý chính nhưng mạch lạc hơn.
        """,
        "analys_prompt": lambda messages: f"""
            From the given query, translate it to English if necessary, then provide exactly one concise English search query (no explanations, no extra options) that a user would use to find relevant information on the web. Query: {messages}
        """,
        "process_link": lambda url, content: f"""
            Nội dung từ {url}:\n{content}\n
            Đọc kỹ nội dung trên và trả lời câu hỏi dưới dạng bullet points ngắn gọn:
            - Nội dung chính đang nói về gì?
            - Có những điểm quan trọng nào cần nhớ?
            - Thông tin này có đáng tin không? Vì sao?
            Trả lời theo dạng bullet, ngắn gọn để người đọc dễ nắm bắt.
        """,
    }
    return task_handlers.get(task_type, lambda: "Invalid task type")
