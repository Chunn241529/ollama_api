import json
import logging
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
    """Tạo prompt để tóm tắt lịch sử chat."""
    return [{
        "role": "system",
        "content": """Với vai trò là một AI assistant chuyên nghiệp, hãy tóm tắt cuộc hội thoại sau một cách hiệu quả:
                     1. Chỉ giữ lại những thông tin quan trọng nhất và context cần thiết
                     2. Tập trung vào các yêu cầu, quyết định và kết luận chính
                     3. Bỏ qua các chi tiết thừa và hội thoại không quan trọng
                     4. Viết ngắn gọn, súc tích nhưng vẫn đảm bảo đủ context để hiểu
                     5. Giữ lại các tham số kỹ thuật hoặc cấu hình quan trọng nếu có
                     Mục tiêu: Tạo ra một bản tóm tắt, giữ được tất cả thông tin cần thiết."""
    }, {
        "role": "user",
        "content": f"Tóm tắt cuộc hội thoại sau thành một đoạn ngắn gọn:\n\n{history_str}"
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
    """Tóm tắt lịch sử chat khi vượt quá số tin nhắn hoặc số ký tự, tránh tóm tắt lặp lại."""
    from .chat_stream import stream_response_history

    try:
        if storage is not None:
            if isinstance(storage, DatabaseHistoryStorage) and chat_ai_id is None:
                logger.warning("chat_ai_id is required for DatabaseHistoryStorage")
                return []
            history = await storage.get_history(chat_ai_id)
        else:
            if not history:
                return []

        total_chars = sum(len(m["content"]) for m in history)
        logger.debug(f"History: {len(history)} messages, {total_chars} characters")

        has_summary = any(
            m["role"] == "system" and m["content"].startswith("Context từ cuộc hội thoại trước:")
            for m in history
        )

        # Chỉ tóm tắt khi có đủ 5 đoạn hội thoại (user+assistant)
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

        if num_turns < max_history_length:
            logger.debug("No summarization needed: not enough turns")
            return history

        # Nếu history chỉ còn 1 message system context thì không tóm tắt nữa
        if (
            len(history) == 1
            and history[0]["role"] == "system"
            and (
                history[0]["content"].startswith("Context của cuộc hội thoại")
                or history[0]["content"].startswith("Context từ cuộc hội thoại trước:")
            )
        ):
            logger.debug("No summarization needed: only context message present")
            return history

        # Tìm vị trí context system gần nhất (nếu có)
        context_idx = -1
        for idx, m in enumerate(history):
            if m["role"] == "system" and (
                m["content"].startswith("Context của cuộc hội thoại") or
                m["content"].startswith("Context từ cuộc hội thoại trước:")
            ):
                context_idx = idx

        # Các đoạn cần tóm tắt là trước context system gần nhất (hoặc toàn bộ nếu chưa từng tóm tắt)
        history_to_summarize = history[:context_idx] if context_idx != -1 else history
        history_after_context = history[context_idx+1:] if context_idx != -1 else []

        # Đếm số đoạn user+assistant trong phần cần tóm tắt
        def count_turns(hist):
            count = 0
            i = 0
            while i < len(hist) - 1:
                if hist[i]["role"] == "user" and hist[i+1]["role"] == "assistant":
                    count += 1
                    i += 2
                else:
                    i += 1
            return count
        num_turns = count_turns(history_to_summarize)
        logger.debug(f"Number of user+assistant turns to summarize: {num_turns}")
        if num_turns < max_history_length:
            logger.debug("No summarization needed: not enough turns before context")
            return history

        # Nếu history_to_summarize rỗng, không tóm tắt
        if not history_to_summarize:
            logger.debug("No summarization needed: nothing to summarize")
            return history

        # Tóm tắt phần trước context, giữ lại phần sau context
        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history_to_summarize])
        summary_prompt = _create_summary_prompt(history_str)

        summary = ""
        async for chunk in stream_response_history(
            session=session,
            messages=summary_prompt,
            model="4T-Small:latest",
            temperature=0.3,
            max_tokens=-1,
            url_local=url_local,
        ):
            if isinstance(chunk, bytes):
                chunk = chunk.decode('utf-8')
            try:
                chunk_data = json.loads(chunk)
                if chunk_data.get("message", {}).get("content"):
                    summary += chunk_data["message"]["content"]
            except json.JSONDecodeError:
                continue

        if not summary.strip():
            logger.warning("Empty summary generated, falling back to original history")
            return history

        # Kết quả: context system mới + các đoạn sau context cũ
        summarized_history = [{
            "role": "system",
            "content": f"Context của cuộc hội thoại:\n{summary.strip()}"
        }] + history_after_context

        if storage:
            await storage.clear_history(chat_ai_id)
            for msg in summarized_history:
                await storage.add_message(msg["role"], msg["content"], chat_ai_id)
            logger.debug(f"Updated storage with summarized history: {len(summarized_history)} messages")

        return summarized_history

    except Exception as e:
        logger.error(f"Error in summarize_chat_history: {str(e)}")
        return history[-max_history_length:] if history else []
