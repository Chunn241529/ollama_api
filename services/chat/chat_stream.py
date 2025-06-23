import json
import logging
from datetime import datetime
from typing import AsyncGenerator, Dict, Any
import aiohttp
import asyncio

from config.settings import OLLAMA_API_URL
from .utils import prepare_payload
from .history_storage import HistoryStorage, DatabaseHistoryStorage

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
                        # logger.debug(f"Processing chunk: {chunk_data}")
                        if is_type == "thinking" and not chunk_data.get("message", {}).get("content"):
                            logger.warning("Empty content in thinking chunk")
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
                logger.debug(f"Final chunk: {chunk_data}")
                yield json.dumps(chunk_data, ensure_ascii=False) + "\n"
            except json.JSONDecodeError:
                pass

async def _make_api_request(session, url: str, payload: Dict[str, Any], is_type: str) -> AsyncGenerator[str, None]:
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
    session,
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
        from .history_manager import summarize_chat_history

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

            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = prepare_payload(model, full_messages, temperature, max_tokens, top_p)
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
    session,
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
        from .history_manager import summarize_chat_history

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

            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = prepare_payload("gemma3:4b-it-qat", full_messages, temperature, max_tokens, top_p)
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
    session,
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
        from .history_manager import summarize_chat_history

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

            user_messages = [msg for msg in messages if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = prepare_payload(model, full_messages, temperature, max_tokens, top_p)
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

async def stream_response_deepsearch(
    session,
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
        from .history_manager import summarize_chat_history
        from .utils import get_task_handler

        if not task_type:
            logger.error("Task type is required for deepsearch")
            yield json.dumps({
                "error": "Task type is required",
                "type": "error",
                "created": int(datetime.now().timestamp()),
                "status": 400,
            }, ensure_ascii=False) + "\n"
            return

        handler = get_task_handler(task_type)
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

            if isinstance(messages, dict) and messages.get("role") == "user":
                await storage.add_message(messages["role"], messages["content"], chat_ai_id)
            elif isinstance(messages, list):
                user_messages = [msg for msg in messages if msg.get("role") == "user"]
                if user_messages:
                    await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = prepare_payload(model, full_messages, temperature, max_tokens, top_p)
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

async def stream_response_history(
    session,
    messages: list,
    model: str = "qwen2.5vl:7b",
    temperature: float = 0.3,
    max_tokens: int = -1,
    url_local: str = OLLAMA_API_URL,
) -> AsyncGenerator[str, None]:
    """Stream response chỉ cho tóm tắt history, không thêm system prompt AI."""
    try:
        payload = prepare_payload(model, messages, temperature, max_tokens)
        logger.debug("Sending history summary payload")
        async for chunk in _make_api_request(session, f"{url_local}/api/chat", payload, "text"):
            yield chunk
    except Exception as e:
        logger.error(f"Unexpected error in stream_response_history: {str(e)}")
        yield json.dumps({
            "error": f"Unexpected error: {str(e)}",
            "type": "error",
            "created": int(datetime.now().timestamp()),
            "status": 500,
        }, ensure_ascii=False) + "\n"
