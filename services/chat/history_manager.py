import json
import logging
import aiohttp
from functools import lru_cache
from typing import List, Dict
from datetime import datetime

from .utils import prepare_payload
from .history_storage import HistoryStorage, DatabaseHistoryStorage

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

@lru_cache(maxsize=100)
def _create_summary_prompt(history_str: str) -> list:
    """Tạo prompt để tóm tắt lịch sử chat với yêu cầu chi tiết hơn."""
    return [{
        "role": "system",
        "content": """Với vai trò là một AI assistant chuyên nghiệp, hãy tóm tắt cuộc hội thoại sau một cách chi tiết và hiệu quả:
                     1. Giữ lại các thông tin quan trọng nhất, bao gồm context, yêu cầu chính, và câu trả lời nổi bật.
                     2. Đặc biệt giữ nguyên các đoạn code Python hoặc tham số kỹ thuật (nếu có) trong định dạng code block (```python ... ```).
                     3. Tập trung vào các quyết định, kết luận, và các ví dụ cụ thể được cung cấp.
                     4. Bỏ qua các chi tiết thừa như câu chào hỏi thông thường, nhưng giữ lại các chi tiết liên quan đến yêu cầu kỹ thuật.
                     5. Viết tóm tắt ngắn gọn nhưng đầy đủ, với độ dài tối thiểu 50 từ để đảm bảo đủ chi tiết.
                     6. Đảm bảo tóm tắt rõ ràng, dễ hiểu để AI có thể sử dụng làm context cho các câu hỏi tiếp theo.
                     Mục tiêu: Tạo bản tóm tắt giữ được tất cả thông tin kỹ thuật quan trọng và context cần thiết."""
    }, {
        "role": "user",
        "content": f"Tóm tắt cuộc hội thoại sau thành một đoạn chi tiết:\n\n{history_str}"
    }]

async def summarize_chat_history(
    session,
    history: list = None,
    max_history_length: int = 5,
    max_total_chars: int = 2500,
    url_local: str = None,
    storage: HistoryStorage = None,
    chat_ai_id: int = None,
) -> list:
    """Tóm tắt lịch sử chat khi vượt quá số tin nhắn hoặc số ký tự, cho phép tóm tắt lại nếu vượt ngưỡng."""
    from .chat_stream import stream_response_history

    try:
        if storage is not None:
            if isinstance(storage, DatabaseHistoryStorage) and chat_ai_id is None:
                logger.warning("chat_ai_id is required for DatabaseHistoryStorage")
                return []
            history = await storage.get_history(chat_ai_id)
        else:
            if not history:
                logger.debug("No history provided, returning empty list")
                return []

        total_chars = sum(len(m["content"]) for m in history)
        logger.debug(f"History: {len(history)} messages, {total_chars} characters")

        # Đếm số đoạn hội thoại (cặp user + assistant)
        def count_turns(history):
            count = 0
            i = 0
            while i < len(history) - 1:
                if history[i]["role"] == "user" and history[i+1]["role"] == "assistant":
                    count += 1
                    i += 2
                else:
                    i += 1
            return count

        num_turns = count_turns(history)
        logger.debug(f"Number of user+assistant turns: {num_turns}")

        # Kiểm tra nếu lịch sử đã được tóm tắt
        has_summary = any(
            m["role"] == "system" and m["content"].startswith("Context của cuộc hội thoại:")
            for m in history
        )
        logger.debug(f"Has existing summary: {has_summary}")

        # Chỉ bỏ qua tóm tắt nếu chưa vượt ngưỡng
        if has_summary and num_turns < max_history_length and total_chars < max_total_chars:
            logger.debug("No summarization needed: history already summarized and within limits")
            return history

        # Tóm tắt nếu số đoạn hội thoại >= max_history_length hoặc tổng ký tự >= max_total_chars
        if num_turns < max_history_length and total_chars < max_total_chars:
            logger.debug("No summarization needed: not enough turns or characters")
            return history

        # Kiểm tra url_local
        if not url_local or url_local.strip() == "":
            logger.error("url_local is None or empty, cannot proceed with summarization")
            return history[-max_history_length*2:] if history else []  # Giữ 2 lần max_history_length để bảo toàn cặp user+assistant

        # Tóm tắt lịch sử
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history])
        summary_prompt = _create_summary_prompt(history_str)

        summary = ""
        try:
            async for chunk in stream_response_history(
                session=session,
                messages=summary_prompt,
                model="4T-Small:latest",
                temperature=0.3,
                max_tokens=500,
                url_local=url_local,
            ):
                logger.debug(f"Raw chunk received: {chunk}")
                if isinstance(chunk, bytes):
                    chunk = chunk.decode('utf-8')
                try:
                    if isinstance(chunk, str):
                        chunk_data = json.loads(chunk)
                        content = chunk_data.get("message", {}).get("content", "")
                        if content:
                            summary += content
                        else:
                            logger.warning(f"No content in chunk: {chunk}")
                    else:
                        logger.warning(f"Unexpected chunk type: {type(chunk)}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse chunk: {chunk}, error: {str(e)}")
                    continue
                except Exception as e:
                    logger.warning(f"Error processing chunk: {str(e)}")
                    continue
        except aiohttp.ClientError as e:
            logger.error(f"Network error during stream_response_history: {str(e)}")
            return history[-max_history_length*2:] if history else []

        if not summary.strip():
            logger.warning("Empty summary generated, falling back to last max_history_length messages")
            return history[-max_history_length*2:] if history else []

        # Kiểm tra độ dài tóm tắt
        if len(summary.split()) < 50:
            logger.warning(f"Summary too short ({len(summary.split())} words), falling back to last max_history_length messages")
            return history[-max_history_length*2:] if history else []

        # Tạo lịch sử mới với tin nhắn system context
        summarized_history = [{
            "role": "assistant",
            "content": f"Context của cuộc hội thoại (history):\n{summary.strip()}"
        }]
        logger.debug(f"Generated summary: {summary.strip()}")

        if storage:
            await storage.clear_history(chat_ai_id)
            for msg in summarized_history:
                await storage.add_message(msg["role"], msg["content"], chat_ai_id)
            logger.debug(f"Updated storage with summarized history: {len(summarized_history)} messages")

        return summarized_history

    except Exception as e:
        logger.error(f"Error in summarize_chat_history: {str(e)}")
        return history[-max_history_length*2:] if history else []
