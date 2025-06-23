import subprocess
import textwrap
import json
import logging
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import StreamingResponse, FileResponse
import aiohttp
from models.chat import ChatRequest, SavePartialRequest
from dependencies.auth import verify_token, call_api_get_dbname
from services.chat import (
    stream_response_normal,
    stream_response_deepthink,
    stream_response_deepsearch,
    stream_response_image,
    DatabaseHistoryStorage,
    ListHistoryStorage,
    summarize_chat_history
)
from services.repository.repo_client import RepositoryClient
from services.func.search import extract_search_info, search_duckduckgo_unlimited
from config.settings import DEFAULT_CUSTOM_AI, DEFAULT_THINK_AI
from services.deepsearch import deepsearch
import os
import re
import base64
import shutil
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

# Global ListHistoryStorage instance for /test endpoint with JSON file
TEST_STORAGE = ListHistoryStorage(file_path="storage/log/wrap_history.json")

def extract_image_info(prompt):
    """Extract image URL or path and description from prompt."""
    url_pattern = r'(https?://[^\s]+|file://[^\s]+)'
    match = re.search(url_pattern, prompt)
    if match:
        image_source = match.group(0)
        description = prompt.replace(image_source, "").strip()
        if not description:
            description = "Mô tả từng chi tiết của hình ảnh."
        return image_source, description
    elif "data:image" in prompt:
        parts = prompt.split(",", 1)
        if len(parts) == 2:
            description = parts[0].split("data:image")[0].strip()
            if not description:
                description = "Mô tả từng chi tiết của hình ảnh."
            return parts[1].strip(), description
    return None, None

async def classify_user_intent(prompt):
    """Dùng AI để phân loại ý định user: image, code, hay normal."""
    system_prompt = (
        "Bạn là một AI phân loại yêu cầu của người dùng. "
        "Hãy trả lời duy nhất một từ trong các lựa chọn sau: 'image', 'code', 'normal'.\n"
        "Nếu người dùng muốn tạo ảnh, trả lời 'image'.\n"
        "Nếu người dùng muốn tạo code, trả lời 'code'.\n"
        "Nếu là trò chuyện thông thường, trả lời 'normal'.\n"
        "Chỉ trả về đúng 1 từ, không giải thích gì thêm.\n"
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    try:
        async with aiohttp.ClientSession() as session:
            async for chunk in stream_response_normal(
                session=session,
                model=DEFAULT_CUSTOM_AI,
                messages=messages,
                storage=TEST_STORAGE
            ):
                try:
                    chunk_data = json.loads(chunk)
                    content = chunk_data.get("message", {}).get("content", "").strip().lower()
                    if content in ["image", "code", "normal"]:
                        return content
                except Exception:
                    continue
    except Exception:
        pass
    return None

@router.post("/send")
async def chat(chat_request: ChatRequest, current_user: dict = Depends(verify_token)):
    """Send chat request to Ollama API and stream response."""
    prompt = chat_request.prompt
    model = chat_request.model
    chat_ai_id = chat_request.chat_ai_id
    is_deep_think = chat_request.is_deep_think
    is_search = chat_request.is_search
    is_deepsearch = chat_request.is_deepsearch

    if not chat_ai_id:
        raise HTTPException(status_code=400, detail="chat_ai_id is required for /send endpoint")

    username = current_user["username"]
    db_path = await call_api_get_dbname(username)
    repo = RepositoryClient(db_path)
    storage = DatabaseHistoryStorage(repo)

    custom_ai = repo.get_custom_chat_ai_by_id(chat_ai_id)
    if not custom_ai:
        raise HTTPException(status_code=404, detail=f"Custom AI for chat_ai_id {chat_ai_id} not found")
    custom_ai_text = custom_ai[0]

    image_source, image_text = extract_image_info(prompt)

    async def generate():
        async with aiohttp.ClientSession(
            connector=aiohttp.TCPConnector(limit=100, ttl_dns_cache=300),
            timeout=aiohttp.ClientTimeout(total=60, connect=10)
        ) as session:
            try:
                if image_source:
                    messages = [{
                        "role": "user",
                        "content": image_text,
                        "images": [image_source]
                    }]
                    response_content = ""
                    async for chunk in stream_response_image(
                        session=session,
                        model=model,
                        messages=messages,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    ):
                        if isinstance(chunk, bytes):
                            chunk = chunk.decode('utf-8')
                        try:
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("message", {}).get("content"):
                                response_content += chunk_data["message"]["content"]
                        except json.JSONDecodeError:
                            pass
                        yield chunk
                    if response_content:
                        await storage.add_message("assistant", response_content, chat_ai_id)
                elif is_deep_think:
                    messages = [{"role": "system", "content": custom_ai_text}]
                    history = await storage.get_history(chat_ai_id)
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    )
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})

                    debate_prompt = textwrap.dedent(
                        """
                        Bạn là một trợ lý AI với khả năng tư duy sâu và tự nhiên như con người.
                        Hãy mô phỏng quá trình suy nghĩ của bạn theo ngôi thứ nhất và trình bày rõ ràng, chi tiết các bước giải quyết vấn đề.
                        Bạn đóng vai một lập trình viên xuất sắc, luôn tìm tòi, kiểm chứng và cải thiện giải pháp của mình.
                        Các bước bạn cần tuân thủ:
                        1. Bắt đầu câu trả lời với câu: "Okey, vấn đề của user là '{prompt}'."
                        2. Chia nhỏ vấn đề thành các phần logic như: nguyên nhân, hậu quả và giải pháp.
                        3. Kiểm tra độ chính xác của dữ liệu và tính logic của các lập luận.
                        4. Diễn đạt lại ý tưởng một cách đơn giản, rõ ràng, tránh sử dụng các thuật ngữ phức tạp.
                        5. Luôn tự hỏi "Còn cách nào tốt hơn không?" để cải thiện chất lượng giải pháp.
                        6. Khi cần, hãy đính kèm các tài liệu liên quan như đoạn code hoặc các nguồn tham khảo bổ sung.
                        """
                    ).format(prompt=prompt)
                    brain_think = [{"role": "user", "content": debate_prompt}]
                    response_content = ""
                    async for chunk in stream_response_deepthink(
                        session=session,
                        messages=brain_think,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    ):
                        try:
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("message", {}).get("content"):
                                response_content += chunk_data["message"]["content"]
                        except json.JSONDecodeError:
                            pass
                        yield chunk
                    if response_content:
                        await storage.add_message("assistant", response_content, chat_ai_id)

                    refined_prompt = textwrap.dedent(
                        f"""
                        Dựa trên phân tích "{response_content}", hãy đưa ra kết luận cuối cùng cho câu hỏi: "{prompt}" đầy đủ và logic nhất.
                        """
                    ).strip()
                    messages.append({"role": "user", "content": refined_prompt})
                    response_content = ""
                    async for chunk in stream_response_normal(
                        session=session,
                        model=model,
                        messages=messages,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    ):
                        try:
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("message", {}).get("content"):
                                response_content += chunk_data["message"]["content"]
                        except json.JSONDecodeError:
                            pass
                        yield chunk
                    if response_content:
                        await storage.add_message("assistant", response_content, chat_ai_id)
                elif is_search:
                    messages = [{"role": "system", "content": custom_ai_text}]
                    history = await storage.get_history(chat_ai_id)
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    )
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})

                    search_results = search_duckduckgo_unlimited(prompt)
                    if search_results:
                        extracted_info = extract_search_info(search_results)
                        search_prompt = f"""
                            Kết quả tìm kiếm: \n"{extracted_info}"\n Dựa vào kết quả tìm kiếm trên, hãy cung cấp thêm thông tin 'body' và 'href' của website đó.
                        """
                        messages.append({"role": "user", "content": search_prompt})
                        response_content = ""
                        async for chunk in stream_response_normal(
                            session=session,
                            model=model,
                            messages=messages,
                            storage=storage,
                            chat_ai_id=chat_ai_id
                        ):
                            try:
                                chunk_data = json.loads(chunk)
                                if chunk_data.get("message", {}).get("content"):
                                    response_content += chunk_data["message"]["content"]
                            except json.JSONDecodeError:
                                pass
                            yield chunk
                        if response_content:
                            await storage.add_message("assistant", response_content, chat_ai_id)
                elif is_deepsearch:
                    messages = [{"role": "system", "content": custom_ai_text}]
                    history = await storage.get_history(chat_ai_id)
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    )
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})

                    response_content = ""
                    async for chunk in deepsearch(
                        messages=messages,
                        session=session,
                        model=model,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    ):
                        try:
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("type") == "deepsearch" and chunk_data.get("message", {}).get("content"):
                                response_content += chunk_data["message"]["content"]
                        except json.JSONDecodeError:
                            pass
                        yield chunk
                    if response_content:
                        await storage.add_message("assistant", response_content, chat_ai_id)
                else:
                    messages = [{"role": "system", "content": custom_ai_text}]
                    history = await storage.get_history(chat_ai_id)
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    )
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})

                    response_content = ""
                    async for chunk in stream_response_normal(
                        session=session,
                        model=model,
                        messages=messages,
                        storage=storage,
                        chat_ai_id=chat_ai_id
                    ):
                        try:
                            chunk_data = json.loads(chunk)
                            if chunk_data.get("message", {}).get("content"):
                                response_content += chunk_data["message"]["content"]
                        except json.JSONDecodeError:
                            pass
                        yield chunk
                    if response_content:
                        await storage.add_message("assistant", response_content, chat_ai_id)

            except aiohttp.ClientError as e:
                error_msg = f"Connection error: {str(e)}"
                yield json.dumps({"error": error_msg, "type": "error"}, ensure_ascii=False)
            except Exception as e:
                error_msg = f"Unexpected error: {str(e)}"
                yield json.dumps({"error": error_msg, "type": "error"}, ensure_ascii=False)
            # KHÔNG gọi await session.close() ở đây

    return StreamingResponse(generate(), media_type="text/plain")

@router.post("/test")
async def chat_test(chat_request: ChatRequest):
    """Test chat endpoint without authentication."""
    prompt = chat_request.prompt
    model = chat_request.model
    is_deep_think = chat_request.is_deep_think
    is_deepsearch = chat_request.is_deepsearch

    # Dùng AI để phân loại ý định user (không truyền session vào)
    user_intent = await classify_user_intent(prompt)
    prompt_lower = prompt.lower().strip()
    if user_intent == "image":
        is_image = True
        is_code = False
    elif user_intent == "code":
        is_image = False
        is_code = True
    elif user_intent == "normal":
        is_image = False
        is_code = False
    else:
        # fallback: logic cũ
        image_prefixes = [
            "tạo ảnh", "tạo hình ảnh", "vẽ ảnh", "generate image", "create image", "draw image"
        ]
        is_image = any(prompt_lower.startswith(prefix) for prefix in image_prefixes)
        is_code = any(kw in prompt_lower for kw in ["code", "mã nguồn", "lập trình", "viết chương trình", "python", "javascript", "html", "css", "c++", "java", "golang", "typescript"])
    is_normal = not is_image and not is_code

    # Model selection
    if is_code:
        selected_model = "qwen2.5-coder:14b-instruct"
    elif is_image:
        selected_model = None  # handled by generate_image
    else:
        selected_model = model or DEFAULT_CUSTOM_AI

    async def generate():
        async with aiohttp.ClientSession() as session:
            try:
                image_source, image_text = extract_image_info(prompt)
                if is_image:
                    # Use generate_image for image requests
                    from services.img import generate_image
                    result = await generate_image(prompt_text=prompt)
                    if "image_path" in result and "mime_type" in result:
                        try:
                            async with session.post(
                                "http://localhost:2401/chat/process_image",
                                json={"file_path": result["image_path"]}
                            ) as response:
                                if response.status != 200:
                                    logger.error("Failed to convert image to base64: %s", response.status)
                                    yield json.dumps({
                                        "type": "error",
                                        "message": f"Failed to convert image to base64: {response.status}"
                                    }, ensure_ascii=False).encode("utf-8")
                                else:
                                    base64_data = await response.json()
                                    yield json.dumps({
                                        "type": "image",
                                        "image_base64": base64_data["base64"],
                                        "mime_type": result["mime_type"]
                                    }, ensure_ascii=False).encode("utf-8")
                        except aiohttp.ClientError as e:
                            logger.error("Error converting image to base64: %s", str(e))
                            yield json.dumps({
                                "type": "error",
                                "message": f"Error converting image to base64: {str(e)}"
                            }, ensure_ascii=False).encode("utf-8")
                    else:
                        yield json.dumps({
                            "type": "error",
                            "message": result.get("error", "Failed to generate image")
                        }, ensure_ascii=False).encode("utf-8")
                elif is_code:
                    messages = [{"role": "system", "content": DEFAULT_CUSTOM_AI}]
                    history = await TEST_STORAGE.get_history()
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=TEST_STORAGE
                    )
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})
                    async for chunk in stream_response_normal(
                        session=session,
                        model=selected_model,
                        messages=messages,
                        storage=TEST_STORAGE
                    ):
                        yield chunk
                elif is_deep_think:
                    logger.debug(f"Processing deepthink request with prompt: {prompt}")
                    messages = [{"role": "system", "content": DEFAULT_THINK_AI}]
                    history = await TEST_STORAGE.get_history()
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=TEST_STORAGE
                    )
                    logger.debug(f"Deepthink history: {history}")
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})
                    response_content = ""
                    async for chunk in stream_response_deepthink(
                        session=session,
                        messages=messages,
                        storage=TEST_STORAGE
                    ):
                        try:
                            chunk_data = json.loads(chunk)
                            logger.debug(f"Deepthink chunk sent: {chunk_data}")
                            if chunk_data.get("message", {}).get("content"):
                                response_content += chunk_data["message"]["content"]
                        except json.JSONDecodeError:
                            pass
                        yield chunk
                    if response_content:
                        await TEST_STORAGE.add_message("assistant", response_content)
                    refined_prompt = f"""
                    Hãy xem lại suy nghĩ của bạn: "{response_content}".
                    Giờ, trả lời câu hỏi "{prompt}" một cách rõ ràng và tự nhiên nhất, như đang trò chuyện với một người bạn.
                    - Tập trung vào ý chính, giải thích dễ hiểu, tránh dùng từ ngữ quá phức tạp.
                    - Tổng hợp các điểm quan trọng từ suy nghĩ trước để đưa ra câu trả lời logic và đầy đủ.
                    """
                    messages.append({"role": "user", "content": refined_prompt})
                    async for chunk in stream_response_normal(
                        session=session,
                        model=selected_model,
                        messages=messages,
                        storage=TEST_STORAGE
                    ):
                        yield chunk
                elif is_deepsearch:
                    messages = [{"role": "system", "content": DEFAULT_CUSTOM_AI}]
                    history = await TEST_STORAGE.get_history()
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=TEST_STORAGE
                    )
                    logger.debug(f"Deepsearch history: {history}")
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})
                    async for chunk in deepsearch(
                        messages=messages,
                        session=session,
                        model=selected_model,
                        storage=TEST_STORAGE
                    ):
                        yield chunk
                else:
                    # Normal chat
                    messages = [{"role": "system", "content": DEFAULT_CUSTOM_AI}]
                    history = await TEST_STORAGE.get_history()
                    history = await summarize_chat_history(
                        session=session,
                        history=history,
                        max_history_length=10,
                        storage=TEST_STORAGE
                    )
                    logger.debug(f"Normal history: {history}")
                    messages.extend(history)
                    messages.append({"role": "user", "content": prompt})
                    async for chunk in stream_response_normal(
                        session=session,
                        model=selected_model,
                        messages=messages,
                        storage=TEST_STORAGE
                    ):
                        yield chunk

            except aiohttp.ClientError as e:
                yield json.dumps({
                    "type": "error",
                    "message": f"Connection error: {str(e)}"
                }, ensure_ascii=False).encode("utf-8")
            except Exception as e:
                yield json.dumps({
                    "type": "error",
                    "message": f"Unexpected error: {str(e)}"
                }, ensure_ascii=False).encode("utf-8")

    return StreamingResponse(generate(), media_type="text/plain")

@router.post("/download_image")
async def download_image(request: dict):
    """Download an image based on its file path."""
    image_path = request.get("image_path")
    if not image_path or not isinstance(image_path, str):
        logger.error("Invalid image path: %s", image_path)
        raise HTTPException(status_code=400, detail="Invalid image path provided.")

    if not os.path.exists(image_path):
        logger.error("Image file does not exist: %s", image_path)
        raise HTTPException(status_code=404, detail="Image file not found.")

    if not os.access(image_path, os.R_OK):
        logger.error("No read permissions for image file: %s", image_path)
        raise HTTPException(status_code=403, detail="No read permissions for the image file.")

    ext = os.path.splitext(image_path)[1].lower().lstrip(".")
    mime_type = "image/jpeg" if ext in ["jpg", "jpeg"] else f"image/{ext}" if ext in ["png", "webp", "bmp"] else "image/png"
    logger.info("Serving image: %s, MIME type: %s", image_path, mime_type)

    return FileResponse(
        path=image_path,
        media_type=mime_type,
        filename=f"generated_image.{ext}"
    )

@router.post("/process_image")
async def process_image(request: dict):
    """Process image from URL or file path and return base64."""
    try:
        if "image_url" in request:
            url = request["image_url"]
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(url) as response:
                        if response.status != 200:
                            raise HTTPException(
                                status_code=400,
                                detail=f"Không thể tải ảnh từ URL. Status code: {response.status}"
                            )
                        image_data = await response.read()
                        base64_data = base64.b64encode(image_data).decode('utf-8')
                        return {"base64": base64_data}
                except aiohttp.ClientError as e:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Lỗi khi tải ảnh: {str(e)}"
                    )
        elif "file_path" in request:
            file_path = request["file_path"].replace("file://", "")
            if not os.path.exists(file_path):
                raise HTTPException(
                    status_code=404,
                    detail="File không tồn tại"
                )
            try:
                with open(file_path, "rb") as f:
                    image_data = f.read()
                    base64_data = base64.b64encode(image_data).decode('utf-8')
                    return {"base64": base64_data}
            except IOError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Không thể đọc file: {str(e)}"
                )
        else:
            raise HTTPException(
                status_code=400,
                detail="Thiếu image_url hoặc file_path trong request"
            )
    except Exception as e:
        logger.error("Error processing image: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Lỗi xử lý ảnh: {str(e)}"
        )

@router.post("/save_partial")
async def save_partial_response(request: SavePartialRequest):
    try:
        logger.debug(f"Received save partial request: content_length={len(request.content)}, is_thinking={request.is_thinking}")
        storage = TEST_STORAGE
        await storage.add_message("assistant", request.content, request.chat_ai_id)
        return {"message": "Partial response saved successfully"}
    except Exception as e:
        logger.error(f"Error in save_partial_response: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/upload_image")
async def upload_image(file: UploadFile = File(...)):
    """Nhận file upload từ client, lưu vào thư mục tạm và trả về đường dẫn."""
    import shutil
    from pathlib import Path
    upload_dir = Path("storage/uploaded_files")
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"file_path": str(file_path)}
