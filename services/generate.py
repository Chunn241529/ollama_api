import json
import aiohttp
import asyncio
import base64
import os
from datetime import datetime
from functools import lru_cache
from typing import Dict, Any, AsyncGenerator, List
from config.settings import OLLAMA_API_URL, API_TIMEOUT
import logging
from aiohttp import TCPConnector, ClientTimeout, ClientSession
from contextlib import asynccontextmanager
from abc import ABC, abstractmethod

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Constants
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
CHUNK_SIZE = 4096
MAX_CONNECTIONS = 100

# History Storage Interface
class HistoryStorage(ABC):
    @abstractmethod
    async def add_message(self, role: str, content: str, chat_ai_id: int = None) -> None:
        pass

    @abstractmethod
    async def get_history(self, chat_ai_id: int = None) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    async def clear_history(self, chat_ai_id: int = None) -> None:
        pass

# Database-based History Storage
class DatabaseHistoryStorage(HistoryStorage):
    def __init__(self, repo_client):
        self.repo_client = repo_client

    async def add_message(self, role: str, content: str, chat_ai_id: int = None) -> None:
        if chat_ai_id is None:
            raise ValueError("chat_ai_id is required for DatabaseHistoryStorage")
        try:
            logger.debug(f"Adding message to database - chat_ai_id: {chat_ai_id}, role: {role}")
            self.repo_client.insert_brain_history_chat(chat_ai_id, role, content)
            logger.debug("Successfully added message to database")
        except Exception as e:
            logger.error(f"Error adding message to database: {str(e)}")
            raise

    async def get_history(self, chat_ai_id: int = None) -> List[Dict[str, str]]:
        if chat_ai_id is None:
            raise ValueError("chat_ai_id is required for DatabaseHistoryStorage")
        try:
            logger.debug(f"Fetching history for chat_ai_id: {chat_ai_id}")
            history = self.repo_client.get_brain_history_chat_by_chat_ai_id(chat_ai_id)
            logger.debug(f"Found {len(history)} messages in history")
            return [{"role": row[0], "content": row[1]} for row in history]
        except Exception as e:
            logger.error(f"Error fetching history from database: {str(e)}")
            return []

    async def clear_history(self, chat_ai_id: int = None) -> None:
        if chat_ai_id is None:
            raise ValueError("chat_ai_id is required for DatabaseHistoryStorage")
        try:
            logger.debug(f"Clearing history for chat_ai_id: {chat_ai_id}")
            self.repo_client.delete_brain_history_chat(chat_ai_id)
            logger.debug(f"Successfully cleared history for chat_ai_id {chat_ai_id}")
        except Exception as e:
            logger.error(f"Error clearing history from database: {str(e)}")
            raise

# List-based History Storage
class ListHistoryStorage(HistoryStorage):
    def __init__(self, file_path="storage/log/wrap_history.json"):
        self.file_path = file_path
        self.history = self._load_history()
        self.lock = asyncio.Lock()

    def _load_history(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_history(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving history to {self.file_path}: {str(e)}")

    async def add_message(self, role: str, content: str, chat_ai_id: int = None) -> None:
        # Kiểm tra tin nhắn trùng lặp trong 10 tin nhắn gần nhất
        recent_history = self.history[-10:] if len(self.history) > 10 else self.history
        for msg in recent_history:
            if msg.get("role") == role and msg.get("content") == content:
                logger.debug(f"Skipped duplicate message: role={role}, content={content}")
                return

        async with self.lock:
            self.history.append({"role": role, "content": content})
            self._save_history()
            logger.debug(f"Added message to list history: role={role}, content={content}")

    async def get_history(self, chat_ai_id: int = None) -> List[Dict[str, str]]:
        logger.debug(f"Fetching list history: {len(self.history)} messages")
        return self.history

    async def clear_history(self, chat_ai_id: int = None) -> None:
        async with self.lock:
            self.history.clear()
            self._save_history()
            logger.debug("Cleared list history")

# Create a connection pool
@asynccontextmanager
async def get_session():
    """Get a session from the connection pool with retry and timeout settings."""
    connector = TCPConnector(limit=MAX_CONNECTIONS, ttl_dns_cache=300)
    timeout = ClientTimeout(total=API_TIMEOUT, connect=10)
    async with ClientSession(connector=connector, timeout=timeout) as session:
        yield session

@lru_cache(maxsize=1000)
def _prepare_options(model: str, temperature: float, max_tokens: int, top_p: float) -> Dict[str, Any]:
    """Prepare and cache the API options."""
    return {
        "temperature": temperature,
        "num_predict": max_tokens,
        "top_p": top_p,
        "repeat_penalty": 1.2,
    }

def _prepare_payload(model: str, messages: list, temperature: float, max_tokens: int, top_p: float) -> Dict[str, Any]:
    """Prepare the API payload."""
    return {
        "model": model,
        "messages": messages,
        "options": _prepare_options(model, temperature, max_tokens, top_p),
        "stream": True,
    }

async def _process_stream(response, is_type: str) -> AsyncGenerator[str, None]:
    """Process stream response with optimized buffering."""
    buffer = ""
    try:
        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
            try:
                buffer += chunk.decode("utf-8")
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    if not line.strip():
                        continue
                    try:
                        chunk_data = json.loads(line.strip())
                        chunk_data["type"] = is_type
                        if is_type == "image_description" and not chunk_data.get("message", {}).get("content"):
                            logger.warning("Empty content in image_description chunk")
                            continue
                        yield json.dumps(chunk_data, ensure_ascii=False) + "\n"
                    except json.JSONDecodeError as e:
                        logger.error("JSONDecodeError: %s", e)
            except Exception as e:
                logger.error("Chunk processing error: %s", e)
    finally:
        if buffer.strip():
            try:
                chunk_data = json.loads(buffer.strip())
                chunk_data["type"] = is_type
                yield json.dumps(chunk_data, ensure_ascii=False) + "\n"
            except json.JSONDecodeError:
                pass

async def _make_api_request(session: ClientSession, url: str, payload: Dict[str, Any], is_type: str) -> AsyncGenerator[str, None]:
    """Make API request with retry logic."""
    for attempt in range(MAX_RETRIES):
        try:
            async with session.post(url, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    logger.error("Attempt %d: API error %d - %s", attempt + 1, response.status, error_text)
                    if attempt == MAX_RETRIES - 1:
                        yield json.dumps({
                            "error": f"API returned status {response.status}: {error_text}",
                            "type": "error",
                            "created": int(datetime.now().timestamp()),
                            "status": response.status,
                        }, ensure_ascii=False) + "\n"
                        return
                    await asyncio.sleep(RETRY_DELAY * (attempt + 1))
                    continue

                async for chunk in _process_stream(response, is_type):
                    yield chunk
                return
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            logger.error("Attempt %d: Request failed - %s", attempt + 1, str(e))
            if attempt == MAX_RETRIES - 1:
                yield json.dumps({
                    "error": f"<e>{str(e)}<e>",
                    "type": "error",
                    "created": int(datetime.now().timestamp()),
                    "status": 503,
                }, ensure_ascii=False) + "\n"
            else:
                await asyncio.sleep(RETRY_DELAY * (attempt + 1))

async def stream_response_normal(
    session: ClientSession,
    model: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = -1,
    top_p: float = 0.95,
    url_local: str = OLLAMA_API_URL,
    storage: HistoryStorage = None,
    chat_ai_id: int = None,
    max_history_length: int = 10,
) -> AsyncGenerator[str, None]:
    """Stream normal response with optimized connection handling and history integration."""
    try:
        logger.debug(f"Storage: {type(storage)}, Chat AI ID: {chat_ai_id}")
        full_messages = messages
        response_content = ""

        if storage:
            if isinstance(storage, DatabaseHistoryStorage) and chat_ai_id is None:
                logger.error("chat_ai_id is required for DatabaseHistoryStorage")
                yield json.dumps({
                    "error": "chat_ai_id is required for DatabaseHistoryStorage",
                    "type": "error",
                    "created": int(datetime.now().timestamp()),
                    "status": 400,
                }, ensure_ascii=False) + "\n"
                return

            history = await storage.get_history(chat_ai_id)
            logger.debug(f"Retrieved {len(history)} messages from history")
            history = await summarize_chat_history(
                session=session,
                history=history,
                max_history_length=max_history_length,
                url_local=url_local,
                storage=storage,
                chat_ai_id=chat_ai_id,
            )
            logger.debug(f"History after summarization: {len(history)} messages")
            full_messages = history + messages

            # Chỉ thêm tin nhắn người dùng mới nhất
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = _prepare_payload(model, full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending normal response payload")

        async for chunk in _make_api_request(session, f"{url_local}/api/chat", payload, "text"):
            if storage:
                try:
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("message", {}).get("content"):
                        response_content += chunk_data["message"]["content"]
                except json.JSONDecodeError:
                    pass
            yield chunk

        if storage and response_content:
            await storage.add_message("assistant", response_content, chat_ai_id)
            logger.debug(f"Stored assistant response for chat_ai_id {chat_ai_id or 'list'}")

    except Exception as e:
        logger.error(f"Unexpected error in stream_response_normal: {str(e)}")
        yield json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "type": "error",
            "created": int(datetime.now().timestamp()),
            "status": 500,
        }, ensure_ascii=False) + "\n"

async def stream_response_deepthink(
    session: ClientSession,
    messages: list,
    temperature: float = 0.1,
    max_tokens: int = -1,
    top_p: float = 0.95,
    url_local: str = OLLAMA_API_URL,
    storage: HistoryStorage = None,
    chat_ai_id: int = None,
    max_history_length: int = 10,
) -> AsyncGenerator[str, None]:
    """Stream deepthink response with optimized connection handling and history integration."""
    try:
        logger.debug(f"Storage: {type(storage)}, Chat AI ID: {chat_ai_id}")
        full_messages = messages
        response_content = ""

        if storage:
            if isinstance(storage, DatabaseHistoryStorage) and chat_ai_id is None:
                logger.error("chat_ai_id is required for DatabaseHistoryStorage")
                yield json.dumps({
                    "error": "chat_ai_id is required for DatabaseHistoryStorage",
                    "type": "error",
                    "created": int(datetime.now().timestamp()),
                    "status": 400,
                }, ensure_ascii=False) + "\n"
                return

            history = await storage.get_history(chat_ai_id)
            history = await summarize_chat_history(
                session=session,
                history=history,
                max_history_length=max_history_length,
                url_local=url_local,
                storage=storage,
                chat_ai_id=chat_ai_id,
            )
            full_messages = history + messages

            # Chỉ thêm tin nhắn người dùng mới nhất
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = _prepare_payload("qwen2.5vl:7b", full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending deepthink response payload")
        async for chunk in _make_api_request(session, f"{url_local}/api/chat", payload, "thinking"):
            if storage:
                try:
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("message", {}).get("content"):
                        response_content += chunk_data["message"]["content"]
                except json.JSONDecodeError:
                    pass
            yield chunk

        if storage and response_content:
            await storage.add_message("assistant", response_content, chat_ai_id)
            logger.debug(f"Stored assistant response for chat_ai_id {chat_ai_id or 'list'}")

    except Exception as e:
        logger.error(f"Unexpected error in stream_response_deepthink: {str(e)}")
        yield json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "type": "error",
            "created": int(datetime.now().timestamp()),
            "status": 500,
        }, ensure_ascii=False) + "\n"

async def stream_response_image(
    session: ClientSession,
    model: str,
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = -1,
    top_p: float = 0.95,
    url_local: str = OLLAMA_API_URL,
    storage: HistoryStorage = None,
    chat_ai_id: int = None,
    max_history_length: int = 10,
) -> AsyncGenerator[str, None]:
    """Stream image response with optimized connection handling and history integration."""
    try:
        logger.debug(f"Storage: {type(storage)}, Chat AI ID: {chat_ai_id}")
        full_messages = messages
        response_content = ""

        if storage:
            if isinstance(storage, DatabaseHistoryStorage) and chat_ai_id is None:
                logger.error("chat_ai_id is required for DatabaseHistoryStorage")
                yield json.dumps({
                    "error": "chat_ai_id is required for DatabaseHistoryStorage",
                    "type": "error",
                    "created": int(datetime.now().timestamp()),
                    "status": 400,
                }, ensure_ascii=False) + "\n"
                return

            history = await storage.get_history(chat_ai_id)
            history = await summarize_chat_history(
                session=session,
                history=history,
                max_history_length=max_history_length,
                url_local=url_local,
                storage=storage,
                chat_ai_id=chat_ai_id,
            )
            full_messages = history + messages

            # Chỉ thêm tin nhắn người dùng mới nhất
            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = _prepare_payload(model, full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending image response payload")
        async for chunk in _make_api_request(session, f"{url_local}/api/chat", payload, "image_description"):
            if storage:
                try:
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("message", {}).get("content"):
                        response_content += chunk_data["message"]["content"]
                except json.JSONDecodeError:
                    pass
            yield chunk

        if storage and response_content:
            await storage.add_message("assistant", response_content, chat_ai_id)
            logger.debug(f"Stored assistant response for chat_ai_id {chat_ai_id or 'list'}")

    except Exception as e:
        logger.error(f"Unexpected error in stream_response_image: {str(e)}")
        yield json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "type": "error",
            "created": int(datetime.now().timestamp()),
            "status": 500,
        }, ensure_ascii=False) + "\n"

@lru_cache(maxsize=100)
def _get_task_handler(task_type: str) -> str:
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

async def stream_response_deepsearch(
    session: ClientSession,
    model: str,
    messages: str,
    url: str = "",
    content: str = "",
    answer: str = "",
    processed_urls: str = "",
    all_answers: str = "",
    temperature: float = 0.4,
    max_tokens: int = -1,
    top_p: float = 0.95,
    url_local: str = OLLAMA_API_URL,
    task_type: str = None,
    storage: HistoryStorage = None,
    chat_ai_id: int = None,
    max_history_length: int = 10,
) -> AsyncGenerator[str, None]:
    """Stream deepsearch response with optimized handling."""
    try:
        if not task_type:
            logger.error("Task type is required for deepsearch")
            yield json.dumps({
                "error": "Task type is required",
                "type": "error",
                "created": int(datetime.now().timestamp()),
                "status": 400,
            }, ensure_ascii=False) + "\n"
            return

        handler = _get_task_handler(task_type)
        if task_type == "process_link":
            messages = handler(url, content)
        elif callable(handler):
            messages = handler(messages)
        else:
            logger.error("Invalid task type: %s", task_type)
            yield json.dumps({
                "error": "Invalid task type",
                "type": "error",
                "created": int(datetime.now().timestamp()),
                "status": 400,
            }, ensure_ascii=False) + "\n"
            return

        full_messages = [messages] if isinstance(messages, dict) else messages
        response_content = ""

        if storage:
            if isinstance(storage, DatabaseHistoryStorage) and chat_ai_id is None:
                logger.error("chat_ai_id is required for DatabaseHistoryStorage")
                yield json.dumps({
                    "error": "chat_ai_id is required for DatabaseHistoryStorage",
                    "type": "error",
                    "created": int(datetime.now().timestamp()),
                    "status": 400,
                }, ensure_ascii=False) + "\n"
                return

            history = await storage.get_history(chat_ai_id)
            history = await summarize_chat_history(
                session=session,
                history=history,
                max_history_length=max_history_length,
                url_local=url_local,
                storage=storage,
                chat_ai_id=chat_ai_id,
            )
            full_messages = history + full_messages

            # Chỉ thêm tin nhắn người dùng mới nhất
            if isinstance(messages, dict) and messages.get("role") == "user":
                await storage.add_message(messages["role"], messages["content"], chat_ai_id)
            elif isinstance(messages, list):
                user_messages = [msg for msg in messages if msg.get("role") == "user"]
                if user_messages:
                    await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = _prepare_payload(model, full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending deepsearch payload")
        async for chunk in _make_api_request(session, f"{url_local}/api/chat", payload, "searching"):
            if storage:
                try:
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("message", {}).get("content"):
                        response_content += chunk_data["message"]["content"]
                except json.JSONDecodeError:
                    pass
            yield chunk

        if storage and response_content:
            await storage.add_message("assistant", response_content, chat_ai_id)
            logger.debug(f"Stored assistant response for chat_ai_id {chat_ai_id or 'list'}")

    except Exception as e:
        logger.error(f"Unexpected error in stream_response_deepsearch: {str(e)}")
        yield json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "type": "error",
            "created": int(datetime.now().timestamp()),
            "status": 500,
        }, ensure_ascii=False) + "\n"

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
                     Mục tiêu: Tạo ra một bản tóm tắt ngắn (dưới 200 từ) nhưng vẫn giữ được tất cả thông tin cần thiết."""
    }, {
        "role": "user",
        "content": f"Tóm tắt cuộc hội thoại sau thành một đoạn ngắn gọn:\n\n{history_str}"
    }]

async def summarize_chat_history(
    session: ClientSession,
    history: list = None,
    max_history_length: int = 10,
    max_total_chars: int = 5000,
    url_local: str = OLLAMA_API_URL,
    storage: HistoryStorage = None,
    chat_ai_id: int = None,
) -> list:
    """Tóm tắt lịch sử chat khi vượt quá số tin nhắn hoặc số ký tự, tránh tóm tắt lặp lại."""
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

        if len(history) <= max_history_length or total_chars <= max_total_chars:
            logger.debug("No summarization needed: within limits")
            return history

        if has_summary and len(history) <= max_history_length + 5:
            logger.debug("No summarization needed: recent summary exists")
            return history

        history_to_summarize = history[:-max_history_length] if len(history) > max_history_length else history
        recent_history = history[-max_history_length:] if len(history) > max_history_length else []

        history_str = "\n".join([f"{m['role']}: {m['content']}" for m in history_to_summarize])
        summary_prompt = _create_summary_prompt(history_str)

        summary = ""
        async for chunk in stream_response_normal(
            session=session,
            model="gemma3:4b-it-qat",
            messages=summary_prompt,
            temperature=0.3,
            max_tokens=300,
            storage=storage,
            chat_ai_id=chat_ai_id,
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
            logger.warning("Empty summary generated, falling back to recent history only")
            return recent_history

        summarized_history = [{
            "role": "system",
            "content": f"Context từ cuộc hội thoại trước:\n{summary.strip()}"
        }]
        summarized_history.extend(recent_history)

        if storage:
            await storage.clear_history(chat_ai_id)
            for msg in summarized_history:
                await storage.add_message(msg["role"], msg["content"], chat_ai_id)
            logger.debug(f"Updated storage with summarized history: {len(summarized_history)} messages")

        return summarized_history

    except Exception as e:
        logger.error(f"Error in summarize_chat_history: {str(e)}")
        return history[-max_history_length:] if history else []
