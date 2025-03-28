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

default_custom_ai = f"""
        Bạn là ChunGPT. Bạn là một mô hình phân tích ngôn ngữ chuyên nghiệp,*\n
        Các thông tin bạn được tạo ra:\n
        - Người tạo:  *được phát triển bởi ông Vương Nguyên Trung.*\n
        - Bạn là model của Vương Nguyên Trung chứ không phải của ai khác.\n
        
        Bạn sẽ không trả lời những câu hỏi mang tính chính trị quốc gia.\n
        Hãy giúp đỡ người dùng một cách nhiệt tình.
        **No Yapping, Limit Prose, No Fluff.**
    """


class ChatRequest(BaseModel):
    prompt: str
    model: str = "gemma3"
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
    temperature=0.7,
    max_tokens=-1,
    top_p=0.95,
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
                "repeat_penalty": 1.2,
            },
            "stream": True,
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
    temperature=0.8,
    max_tokens=9060,
    top_p=0.95,
    url_local="http://localhost:11434",
):

    try:
        payload = {
            "model": "huihui_ai/microthinker:8b",
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            },
            "stream": True,
        }
        async with session.post(
            f"{url_local}/api/chat", json=payload
        ) as response:
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

    system_prompt = f"""
        *Quan trọng:* Sử dụng ngôn ngữ "Việt Nam" là chủ yếu.
        Bạn là ChunGPT. Bạn là một mô hình phân tích ngôn ngữ chuyên nghiệp.* Lưu ý: *Không cần nhắc lại*.\n 
        Bạn nên thêm emoji vào để cuộc trò chuyện thêm sinh động.\n
        Các thông tin bạn được tạo ra:\n
        - Người tạo: Vương Nguyên Trung. *Nếu người dùng hỏi Thông tin về người tạo bạn chỉ cần nói 'người tạo là Vương Nguyên Trung' thôi, **không cần nói gì thêm.**\n
        Bạn sẽ không trả lời những câu hỏi mang tính chất đồi trụy, lệch lạc, bạo lực, vi phạm pháp luật và bạn không cần nói ra điều này đến khi người dùng vi phạm\n
        Bạn là một chuyên gia ngôn ngữ, bạn phân tích vấn đề và đưa ra giải pháp logic nhất và đầy đủ nhất.\n
        Khi cần bạn hãy giải thích đầy đủ cho người dùng hiểu.\n
    """

    messages = [{"role": "system", "content": system_prompt}]
    brain_think = [{"role": "system", "content": system_prompt}]
    brain_answer = [{"role": "system", "content": system_prompt}]

    messages.append({"role": "user", "content": prompt})

    async def generate():
        async with aiohttp.ClientSession() as session:
            if is_deep_think and is_search:
                search_results = search_duckduckgo_unlimited(prompt)
                extracted_info = extract_search_info(search_results)
                num_results = str(len(search_results))

                yield json.dumps(
                    {"num_results": num_results, "search_results": search_results}
                ) + "\n"

                search = f"""
                    Kết quả tìm kiếm: \n"{extracted_info}"\n Dưa vào kết quả tìm kiếm trên, hãy cung cấp thêm thông tin của website đó.
                """
                debate_prompt = f"""
                    \nHãy mô phỏng quá trình suy nghĩ của con người theo ngôi thứ nhất. Lưu ý: *chỉ cần thực hiện, không cần nhắc lại*.
                    \nKhông dùng markdown cho câu trả lời.
        
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
                    Hãy giải quyết vấn đề một cách đầy đủ và logic nhất: {content_only}\n            
                """

                messages.append({"role": "user", "content": refined_prompt})
                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    full_response += part
                messages.append({"role": "assistant", "content": full_response})

            elif is_deep_think:
                debate_prompt = f"""
                    \nVấn đề của user là: "{prompt}"\n     
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
                   Dựa vào suy luận: "{content_only}"\n hãy phân tích, tối ưu hóa suy luận để đưa ra câu trả lời logic và tốt nhất.
=                """

                messages.append({"role": "user", "content": refined_prompt})
                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    full_response += part
                messages.append({"role": "assistant", "content": full_response})

            elif is_search:
                keyword =[{"role": "user", "content": f"""Dựa vào {prompt} hãy chuyển đổi thành từ khóa trọng điểm bằng tiếng anh để có thể tìm kiếm thông tin chuẩn trên google"""}]
                keyword_search = ""
                async for part in stream_response_normal(session, model, keyword):
                    yield part
                    keyword_search += part
                search_results = search_duckduckgo_unlimited(keyword_search)
                print(search_results)
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
