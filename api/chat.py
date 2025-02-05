from datetime import datetime
import json
import subprocess
import textwrap
import aiohttp
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import asyncio
from service.func.search import extract_search_info, search_duckduckgo_unlimited
from service.respository.repo_client import RepositoryClient
from api.auth import verify_token  # Import verify_token từ auth.py


router = APIRouter()


import httpx


async def call_api_get_dbname(username):
    url = "http://127.0.0.1:2401/auth/db"
    params = {"username_or_email": username}
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            db_path = data.get("db_path")
            if db_path:
                return db_path
    raise HTTPException(status_code=500, detail="Failed to fetch db_path.")


# Models
default_custom_ai = """
    **Bạn là Như Yên. Bạn là nữ.**
    Bạn là một assistant tận tâm.
    Bạn nhiệt huyết và luôn cố gắng thực hiện theo yêu cầu của tôi hết mình và đầy đủ.
    **Trừ tiếng Anh và Tiếng Việt, bạn không đưa ngôn ngữ khác vào.**
    Hãy cố gắng xưng hô cho đúng.
    **No Yapping, Limit Prose, No Fluff.**
"""


class ChatRequest(BaseModel):
    prompt: str
    model: str = "chunn2.0:7b"
    chat_ai_id: int = None
    is_deep_think: bool = False
    is_search: bool = False


class ManagerChat(BaseModel):
    custom_ai: str = default_custom_ai


# service to get available models
def get_available_models():
    try:
        result = subprocess.run(
            ["ollama", "ls"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")
        if lines:
            models = [line.split()[0] for line in lines[1:]]
            return models
        return []
    except subprocess.CalledProcessError as e:
        print("Unable to fetch model list:", e)
        return []


# Endpoints
@router.get("/models")
async def models(current_user: dict = Depends(verify_token)):
    """
    Lấy danh sách các mô hình có sẵn từ API Llama.
    """
    models = get_available_models()
    return {"models": models}


# Endpoints
@router.get("/get_models_test")
async def models_test():
    """
    Lấy danh sách các mô hình có sẵn từ API Llama.
    """
    models = get_available_models()
    return {"models": models}


@router.post("/create-chat")
async def create_chat(request: ManagerChat, current_user: dict = Depends(verify_token)):
    custom_ai = request.custom_ai
    username = current_user["username"]

    db_path = await call_api_get_dbname(username)  # Gọi async function
    repo = RepositoryClient(db_path)

    chat_ai_id = repo.insert_chat_ai(custom_ai)
    return {"chat_ai_id": chat_ai_id, "custom_ai": custom_ai}


@router.get("/get-chat")
async def get_chat(chat_ai_id: int, current_user: dict = Depends(verify_token)):
    """
    Lấy thông tin phiên trò chuyện AI từ cơ sở dữ liệu người dùng.
    """
    username = current_user["username"]

    db_path = await call_api_get_dbname(username)  # Gọi async function
    repo = RepositoryClient(db_path)
    chat_ai = repo.get_chat_ai_by_id(chat_ai_id)
    if not chat_ai:
        raise HTTPException(status_code=404, detail="Chat not found.")
    return chat_ai


@router.get("/history")
async def get_history_chat(chat_ai_id: int, current_user: dict = Depends(verify_token)):
    """
    Lấy lịch sử cuộc trò chuyện từ cơ sở dữ liệu người dùng.
    """
    username = current_user["username"]

    db_path = await call_api_get_dbname(username)  # Gọi async function
    repo = RepositoryClient(db_path)
    history_chat = repo.get_brain_history_chat_by_chat_ai_id(chat_ai_id)
    if not history_chat:
        raise HTTPException(status_code=404, detail="History not found.")
    return history_chat


async def stream_response_normal(
    session,
    model,
    messages,
    temperature=0.4,
    max_tokens=-1,
    top_p=0.9,
    url_local="http://localhost:11434",
):
    # Đảm bảo endpoint này trả về stream
    try:
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
                "top_k": 50,
                "mirostat": 1,
                "mirostat_tau": 0.6,
                "mirostat_eta": 0.6,
            },
            "stream": True,
            "keep_alive": 100,
        }

        async with session.post(f"{url_local}/api/chat", json=payload) as response:
            buffer = ""
            async for chunk in response.content.iter_chunked(1024):
                try:
                    decoded_chunk = chunk.decode("utf-8")
                    buffer += decoded_chunk

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue

                        try:
                            chunk_data = json.loads(line.strip())
                        except json.JSONDecodeError as e:
                            print("JSONDecodeError:", e)
                            continue

                        # Thêm key "type" với giá trị "text"
                        chunk_data["type"] = "text"

                        # Sử dụng ensure_ascii=False để xuất ký tự Unicode đúng dạng
                        yield json.dumps(chunk_data, ensure_ascii=False) + "\n"
                        await asyncio.sleep(0.01)
                except Exception as e:
                    print("Exception while processing chunk:", e)
                    continue

    except aiohttp.ClientError as e:
        error_response = {
            "error": f"<error>{str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"


async def stream_response_deepthink(
    session,
    messages,
    temperature=0.5,
    max_tokens=-1,
    top_p=0.9,
    url_local="http://localhost:11434",
):

    try:
        payload = {
            "model": "smallthinker:latest",
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
                "top_k": 70,
                "mirostat": 1,
                "mirostat_tau": 0.6,
                "mirostat_eta": 0.6,
            },
            "stream": True,
            "keep_alive": 5,
        }

        async with session.post(f"{url_local}/api/chat", json=payload) as response:
            yield "\n"
            buffer = ""
            async for chunk in response.content.iter_chunked(1024):
                try:
                    decoded_chunk = chunk.decode("utf-8")
                    buffer += decoded_chunk

                    while "\n" in buffer:
                        line, buffer = buffer.split("\n", 1)
                        if not line.strip():
                            continue

                        try:
                            chunk_data = json.loads(line.strip())
                        except json.JSONDecodeError as e:
                            print("JSONDecodeError:", e)
                            continue

                        # Thêm key "type" với giá trị "text"
                        chunk_data["type"] = "thinking"

                        # Sử dụng ensure_ascii=False để xuất ký tự Unicode đúng dạng
                        yield json.dumps(chunk_data, ensure_ascii=False) + "\n"
                        await asyncio.sleep(0.01)
                except Exception as e:
                    print("Exception while processing chunk:", e)
                    continue

            yield "\n\n"
    except aiohttp.ClientError as e:
        error_response = {
            "error": f"<error>{str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"


@router.post("/send")
async def chat(chat_request: ChatRequest, current_user: dict = Depends(verify_token)):
    """
    Gửi yêu cầu tới API ollama để nhận phản hồi từ AI.
    """
    prompt = chat_request.prompt
    model = chat_request.model
    chat_ai_id = chat_request.chat_ai_id
    is_deep_think = chat_request.is_deep_think
    is_search = chat_request.is_search

    username = current_user["username"]

    db_path = await call_api_get_dbname(username)
    repo = RepositoryClient(db_path)
    custom_ai = repo.get_custom_chat_ai_by_id(chat_ai_id)
    custom_ai_text = custom_ai[0]

    history_chat = repo.get_brain_history_chat_by_chat_ai_id(chat_ai_id)

    messages = [{"role": "system", "content": custom_ai_text}]
    brain_think = []
    brain_answer = []

    for role, content in history_chat:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": prompt})
    repo.insert_brain_history_chat(chat_ai_id, role="user", content=prompt)

    async def generate():
        async with aiohttp.ClientSession() as session:
            if is_deep_think:
                debate_prompt = textwrap.dedent(
                    f"""
                        Bạn là một trợ lý AI với khả năng tư duy sâu và tự nhiên như con người. 
                        Hãy mô phỏng quá trình suy nghĩ của bạn theo ngôi thứ nhất và trình bày rõ ràng, chi tiết các bước giải quyết vấn đề. 
                        Bạn đóng vai một lập trình viên xuất sắc, luôn tìm tòi, kiểm chứng và cải thiện giải pháp của mình.

                        Lưu ý 1: Tất cả các câu trả lời của bạn phải được trình bày dưới dạng văn bản tự nhiên. 
                        **Quan trọng nhất:** tất cả thông tin cần được diễn đạt một cách tự nhiên và mạch lạc, không có sự phân chia rõ ràng theo các bước hay tiêu đề.

                        Các bước bạn cần tuân thủ:
                        1. Bắt đầu câu trả lời với câu: "Okey, vấn đề của user là '{prompt}'." (bạn có thể điều chỉnh câu mở đầu theo cách tự nhiên của mình).
                        2. Chia nhỏ vấn đề thành các phần logic như: nguyên nhân, hậu quả và giải pháp.
                        3. Kiểm tra độ chính xác của dữ liệu và tính logic của các lập luận.
                        4. Diễn đạt lại ý tưởng một cách đơn giản, rõ ràng, tránh sử dụng các thuật ngữ phức tạp.
                        5. Luôn tự hỏi "Còn cách nào tốt hơn không?" để cải thiện chất lượng giải pháp.
                        6. Khi cần, hãy đính kèm các tài liệu liên quan như đoạn code hoặc các nguồn tham khảo bổ sung.
                    """
                )

                brain_think.append({"role": "user", "content": debate_prompt})
                repo.insert_brain_history_chat(
                    chat_ai_id, role="user", content=debate_prompt
                )

                deepthink_response = ""  # Tạo biến chứa toàn bộ kết quả
                async for part in stream_response_deepthink(session, brain_think):
                    yield part  # Gửi từng phần cho client ngay lập tức
                    deepthink_response += part  # Gom lại toàn bộ câu trả lời

                brain_answer.append(
                    {"role": "assistant", "content": deepthink_response}
                )
                repo.insert_brain_history_chat(
                    chat_ai_id, role="assistant", content=deepthink_response
                )

                # Chỉ lấy nội dung "content" từ brain_answer
                content_only = brain_answer[0]["content"]

                # Tạo refined_prompt với nội dung đã được làm sạch
                refined_prompt = textwrap.dedent(
                    f"""
                    Dựa trên phân tích "{content_only}", hãy đưa ra kết luận cuối cùng cho câu hỏi: "{prompt}" đầy đủ và logic nhất.
                    """
                ).strip()

                messages.append({"role": "user", "content": refined_prompt})
                repo.insert_brain_history_chat(
                    chat_ai_id, role="user", content=refined_prompt
                )

            elif is_search:
                search_results = search_duckduckgo_unlimited(prompt)
                if search_results:
                    extracted_info = extract_search_info(search_results)
                    search = f"""
                        Kết quả tìm kiếm: \n"{extracted_info}"\n Dưa vào kết quả tìm kiếm trên, hãy cung cấp thêm thông tin 'body' và 'href' của website đó.
                    """
                    messages.append({"role": "user", "content": search})
                    repo.insert_brain_history_chat(
                        chat_ai_id, role="user", content=search
                    )

            full_response = ""
            async for part in stream_response_normal(session, model, messages):
                yield part
                full_response += part
            messages.append({"role": "assistant", "content": full_response})
            repo.insert_brain_history_chat(
                chat_ai_id, role="assistant", content=full_response
            )

    return StreamingResponse(generate(), media_type="text/plain")


@router.post("/test")
async def chat_test(chat_request: ChatRequest):
    """
    Gửi yêu cầu tới API ollama để nhận phản hồi từ AI.
    """
    prompt = chat_request.prompt
    model = chat_request.model
    chat_ai_id = chat_request.chat_ai_id
    is_deep_think = chat_request.is_deep_think
    is_search = chat_request.is_search

    messages = []
    brain_think = []
    brain_answer = []

    messages.append({"role": "user", "content": prompt})

    async def generate():
        async with aiohttp.ClientSession() as session:
            if is_deep_think and is_search:
                search_results = search_duckduckgo_unlimited(prompt)
                extracted_info = extract_search_info(search_results)
                num_results = str(len(search_results))

                yield json.dumps({"num_results": num_results}) + "\n"

                search = f"""
                    Kết quả tìm kiếm: \n"{extracted_info}"\n Dưa vào kết quả tìm kiếm trên, hãy cung cấp thêm thông tin của website đó.
                """
                debate_prompt = f"""
                    Bạn là một trợ lý AI với khả năng tư duy sâu và tự nhiên như con người.
                    \nHãy mô phỏng quá trình suy nghĩ của bạn theo ngôi thứ nhất và trình bày rõ ràng, chi tiết các bước giải quyết vấn đề.

                    \nLưu ý: Tất cả các câu trả lời của bạn phải được trình bày dưới dạng văn bản tự nhiên. 
                    \n**Quan trọng nhất:** Không dùng bất kỳ ký tự markdown nào. Tất cả thông tin cần được diễn đạt một cách tự nhiên và mạch lạc, không có sự phân chia rõ ràng theo các bước hay tiêu đề.
                    
                    \nVấn đề của user là: "{prompt}"\n
                    
                    {search}      
                """

                brain_think.append({"role": "user", "content": debate_prompt})

                deepthink_response = ""  # Tạo biến chứa toàn bộ kết quả
                async for part in stream_response_deepthink(session, brain_think):
                    yield part  # Gửi từng phần cho client ngay lập tức
                    deepthink_response += part  # Gom lại toàn bộ câu trả lời

                brain_answer.append(
                    {"role": "assistant", "content": deepthink_response}
                )

                # Chỉ lấy nội dung "content" từ brain_answer
                content_only = brain_answer[0]["content"]

                refined_prompt = f"""
                    Bám sát logic cốt lõi trong phân tích: '{content_only}'
                    \nTrả lời câu hỏi: "{prompt}" với cấu trúc:
                    \n- Giải đáp trực tiếp vấn đề.
                    \n- Nếu có <code> hãy cải hiện code và phát triển thêm. 
                    \n- Nếu cần thiết hãy giải thích đầy đủ.
                    \nĐảm bảo mọi thông tin đều phục vụ trực tiếp cho việc giải quyết "{prompt}".
=                """

                messages.append({"role": "user", "content": refined_prompt})
                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    full_response += part
                messages.append({"role": "assistant", "content": full_response})

            elif is_deep_think:
                debate_prompt = f"""
                    Bạn là một trợ lý AI với khả năng tư duy sâu và phân tích kỹ vấn đề.
                    Hãy giải quyết vấn đề của user.
=                    \nVấn đề của user là: "{prompt}"\n     
                """

                brain_think.append({"role": "user", "content": debate_prompt})

                deepthink_response = ""  # Tạo biến chứa toàn bộ kết quả
                async for part in stream_response_deepthink(session, brain_think):
                    yield part  # Gửi từng phần cho client ngay lập tức
                    deepthink_response += part  # Gom lại toàn bộ câu trả lời

                brain_answer.append(
                    {"role": "assistant", "content": deepthink_response}
                )

                # Chỉ lấy nội dung "content" từ brain_answer
                content_only = brain_answer[0]["content"]

                refined_prompt = f"""
                    Bám sát logic cốt lõi trong phân tích: '{content_only}'
                    \nTrả lời câu hỏi: "{prompt}" với cấu trúc:
                    \n- Giải đáp trực tiếp vấn đề.
                    \n- Nếu có <code> hãy cải hiện code và phát triển thêm. 
                    \n- Nếu cần thiết hãy giải thích đầy đủ.
                    \nĐảm bảo mọi thông tin đều phục vụ trực tiếp cho việc giải quyết "{prompt}".
=                """

                messages.append({"role": "user", "content": refined_prompt})
                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    full_response += part
                messages.append({"role": "assistant", "content": full_response})

            elif is_search:
                search_results = search_duckduckgo_unlimited(prompt)
                if search_results:
                    extracted_info = extract_search_info(search_results)
                    num_results = str(len(search_results))

                    yield json.dumps(
                        {"num_results": num_results, "search_results": search_results}
                    ) + "\n"

                    search = f"""
                        Kết quả tìm kiếm: \n"{extracted_info}"\n Dưa vào kết quả tìm kiếm trên, hãy cung cấp thêm thông tin của website đó.
                    """
                    messages.append({"role": "user", "content": search})
                    full_response = ""
                    async for part in stream_response_normal(session, model, messages):
                        yield part
                        full_response += part
                    messages.append({"role": "assistant", "content": full_response})
            else:

                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    full_response += part
                messages.append({"role": "assistant", "content": full_response})

    return StreamingResponse(generate(), media_type="text/plain")
