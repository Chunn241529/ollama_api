
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


async def classify_user_intent(prompt):
    """Dùng AI để phân loại ý định user: image, code, hay normal."""
    prompt_r = (
        "Bạn là một AI thông minh, có khả năng phân tích và phân loại yêu cầu của người dùng.\n"
        f"Dựa vào yêu cầu: '{prompt}', chỉ trả lời duy nhất một từ trong các lựa chọn sau: 'image', 'code', 'normal'.\n"
        "- Nếu người dùng yêu cầu tạo, vẽ, sinh ra, generate, render, hoặc chỉnh sửa một hình ảnh mới (bao gồm các từ khóa như 'tạo ảnh', 'vẽ', 'sinh ảnh', 'generate image', 'render image', 'edit image', 'make image', 'create image', 'draw', 'thiết kế ảnh', hoặc ngữ cảnh rõ ràng yêu cầu tạo ảnh), trả lời 'image'.\n"
        "- Nếu người dùng yêu cầu tạo prompt, mô tả, gợi ý, hoặc câu lệnh để sử dụng cho việc tạo ảnh mà không yêu cầu AI trực tiếp tạo ảnh, trả lời 'normal'.\n"
        "- Nếu người dùng hỏi về hình ảnh, phân tích ảnh, mô tả ảnh, hoặc nhắc đến ảnh nhưng không yêu cầu tạo hoặc chỉnh sửa ảnh mới, trả lời 'normal'.\n"
        "- Nếu người dùng yêu cầu tạo, viết, chỉnh sửa, hoặc giải thích mã nguồn (code), trả lời 'code'.\n"
        "- Nếu yêu cầu là trò chuyện thông thường hoặc không thuộc các trường hợp trên, trả lời 'normal'.\n"
        "Ưu tiên kiểm tra ý định tạo ảnh trước các trường hợp khác. Chỉ trả về đúng 1 từ, không giải thích gì thêm.\n"
    )

    messages = [
        {"role": "user", "content": prompt_r}
    ]
    try:
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async for chunk in stream_response_normal(
                session=session,
                model="4T-Small:latest",
                messages=messages,
                storage=None
            ):
                try:
                    chunk_data = json.loads(chunk)
                    content = chunk_data.get("message", {}).get("content", "").strip().lower()
                    if content in ["image", "code", "normal"]:
                        logger.debug(f"Type: {content}")
                        return content
                except Exception:
                    continue
    except Exception:
        pass
    return None

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
    """Stream normal response with optimized connection handling and history integration. No system prompt injected."""
    try:
        from .history_manager import summarize_chat_history


        logger.debug(f"Storage: {type(storage)}, Chat AI ID: {chat_ai_id}")
        response_content = ""
        # Chỉ lấy context system và 1-2 message user gần nhất, không nối toàn bộ history cho AI, nhưng vẫn lưu đầy đủ history
        full_messages = []
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
            # Lấy context system (nếu có)
            context_msgs = [m for m in (history or []) if m.get("role") == "system"]
            # Lấy 2 message user gần nhất (nếu có)
            user_msgs = [m for m in (history or []) if m.get("role") == "user"]
            last_user_msgs = user_msgs[-2:] if len(user_msgs) >= 2 else user_msgs
            # Lấy 1 message assistant gần nhất (nếu có)
            assistant_msgs = [m for m in (history or []) if m.get("role") == "assistant"]
            last_assistant_msg = assistant_msgs[-1:] if assistant_msgs else []
            # Ghép lại: context + user gần nhất + assistant gần nhất + message mới
            full_messages = context_msgs + last_user_msgs + last_assistant_msg + (messages or [])

            # Luôn lưu user message mới vào history
            user_messages = [msg for msg in (messages or []) if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)
        else:
            full_messages = messages if messages is not None else []

        payload = prepare_payload("4T-Small:latest", full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending normal response payload (context system + last user/assistant only)")

        response_content = ""
        async for chunk in _make_api_request(session, f"{url_local}/api/chat", payload, "text"):
            # Thu thập response để lưu vào history
            try:
                chunk_data = json.loads(chunk)
                if chunk_data.get("message", {}).get("content"):
                    response_content += chunk_data["message"]["content"]
            except Exception:
                pass
            yield chunk

        # Sau khi nhận xong, lưu assistant response vào history
        if storage and response_content:
            await storage.add_message("assistant", response_content, chat_ai_id)

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
    messages: list = None,
    temperature: float = 0.1,
    max_tokens: int = -1,
    top_p: float = 0.95,
    url_local: str = OLLAMA_API_URL,
    storage: HistoryStorage = None,
    chat_ai_id: int = None,
    max_history_length: int = 10,
) -> AsyncGenerator[str, None]:
    """Stream deepthink response using 4T-Think:latest and stream every chunk with current in_think state."""
    try:
        from .history_manager import summarize_chat_history


        messages = messages if messages is not None else []
        response_content = ""
        # Chỉ lấy context system và 1-2 message user gần nhất, không nối toàn bộ history
        full_messages = []
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
            # Lấy context system (nếu có)
            context_msgs = [m for m in (history or []) if m.get("role") == "system"]
            # Lấy 2 message user gần nhất (nếu có)
            user_msgs = [m for m in (history or []) if m.get("role") == "user"]
            last_user_msgs = user_msgs[-2:] if len(user_msgs) >= 2 else user_msgs
            # Lấy 1 message assistant gần nhất (nếu có)
            assistant_msgs = [m for m in (history or []) if m.get("role") == "assistant"]
            last_assistant_msg = assistant_msgs[-1:] if assistant_msgs else []
            # Ghép lại: context + user gần nhất + assistant gần nhất + message mới
            full_messages = context_msgs + last_user_msgs + last_assistant_msg + (messages or [])

            # Không tự động lưu response mới vào history ở đây, chỉ lưu user message mới nếu cần
            user_messages = [msg for msg in (messages or []) if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)
        else:
            full_messages = messages.copy()

        payload = prepare_payload("4T-Think:latest", full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending deepthink response payload (context system + last user/assistant only)")

        # Stream every chunk with current in_think state
        in_think = False
        tag_open = "<think>"
        tag_close = "</think>"
        buffer = ""
        async for chunk in _make_api_request(session, f"{url_local}/api/chat", payload, "text"):
            try:
                chunk_data = json.loads(chunk)
                content = chunk_data.get("message", {}).get("content", "")
                if not content:
                    yield chunk
                    continue
                buffer += content
                while buffer:
                    if not in_think:
                        idx = buffer.find(tag_open)
                        if idx == -1:
                            out = buffer
                            buffer = ""
                            if out:
                                out_chunk = chunk_data.copy()
                                out_chunk["type"] = "text"
                                out_chunk["in_think"] = False
                                out_chunk["message"] = out_chunk.get("message", {}).copy() if out_chunk.get("message") else {}
                                out_chunk["message"]["content"] = out
                                yield json.dumps(out_chunk, ensure_ascii=False) + "\n"
                            break
                        else:
                            if idx > 0:
                                out = buffer[:idx]
                                out_chunk = chunk_data.copy()
                                out_chunk["type"] = "text"
                                out_chunk["in_think"] = False
                                out_chunk["message"] = out_chunk.get("message", {}).copy() if out_chunk.get("message") else {}
                                out_chunk["message"]["content"] = out
                                yield json.dumps(out_chunk, ensure_ascii=False) + "\n"
                            buffer = buffer[idx + len(tag_open):]
                            in_think = True
                    else:
                        idx = buffer.find(tag_close)
                        if idx == -1:
                            out = buffer
                            buffer = ""
                            if out:
                                out_chunk = chunk_data.copy()
                                out_chunk["type"] = "thinking"
                                out_chunk["in_think"] = True
                                out_chunk["message"] = out_chunk.get("message", {}).copy() if out_chunk.get("message") else {}
                                out_chunk["message"]["content"] = out
                                yield json.dumps(out_chunk, ensure_ascii=False) + "\n"
                            break
                        else:
                            if idx > 0:
                                out = buffer[:idx]
                                out_chunk = chunk_data.copy()
                                out_chunk["type"] = "thinking"
                                out_chunk["in_think"] = True
                                out_chunk["message"] = out_chunk.get("message", {}).copy() if out_chunk.get("message") else {}
                                out_chunk["message"]["content"] = out
                                yield json.dumps(out_chunk, ensure_ascii=False) + "\n"
                            buffer = buffer[idx + len(tag_close):]
                            in_think = False
            except Exception as e:
                logger.error(f"Error processing deepthink chunk: {e}")
                yield chunk

        # Không tự động lưu response mới vào history ở đây

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
    """Stream image response with optimized connection handling and history integration. No system prompt injected."""
    try:
        from .history_manager import summarize_chat_history

        logger.debug(f"Storage: {type(storage)}, Chat AI ID: {chat_ai_id}")
        full_messages = messages if messages is not None else []
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
            full_messages = (history or []) + (messages or [])

            user_messages = [msg for msg in (messages or []) if msg.get("role") == "user"]
            if user_messages:
                await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = prepare_payload(model, full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending image response payload (no system prompt injected)")

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
    """Stream deepsearch response with optimized handling. No system prompt injected."""
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
            full_messages = (history or []) + (full_messages or [])

            if isinstance(messages, dict) and messages.get("role") == "user":
                await storage.add_message(messages["role"], messages["content"], chat_ai_id)
            elif isinstance(messages, list):
                user_messages = [msg for msg in messages if msg.get("role") == "user"]
                if user_messages:
                    await storage.add_message(user_messages[-1]["role"], user_messages[-1]["content"], chat_ai_id)

        payload = prepare_payload(model, full_messages, temperature, max_tokens, top_p)
        logger.debug("Sending deepsearch payload (no system prompt injected)")

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
    model: str = "4T-Small:latest",
    temperature: float = 0.3,
    max_tokens: int = -1,
    url_local: str = OLLAMA_API_URL,
) -> AsyncGenerator[str, None]:
    """Stream response chỉ cho tóm tắt history, không thêm system prompt AI."""
    try:
        payload = prepare_payload(model, messages, temperature, max_tokens,top_p=0.95)
        logger.debug("Sending history summary payload (no system prompt injected)")
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
