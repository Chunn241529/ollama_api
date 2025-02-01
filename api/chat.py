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
    model: str = "llama3.2:3b"
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
    session, model, messages, temperature=0.8, max_tokens=15000, top_p=0.9, stop=None
):
    url_ngrok = "https://c492-171-243-49-133.ngrok-free.app"
    url_local = "http://localhost:11434"
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        if stop:  # Nếu có danh sách stop words thì thêm vào payload
            payload["stop"] = stop

        async with session.post(f"{url_ngrok}/api/chat", json=payload) as response:
            async for chunk in response.content.iter_any():
                try:
                    chunk_data = json.loads(chunk.decode("utf-8"))  # Parse JSON
                    content = chunk_data.get("message", {}).get(
                        "content", ""
                    )  # Lấy nội dung
                    yield content  # Stream nội dung đến client
                    await asyncio.sleep(0.01)
                except json.JSONDecodeError:
                    continue  # Nếu lỗi parse JSON, bỏ qua chunk này
    except aiohttp.ClientError as e:
        yield f"<error>{str(e)}</error>"


async def stream_response_deepthink(
    session, model, messages, temperature=0.5, max_tokens=15000, top_p=0.9, stop=None
):
    url_ngrok = "https://c492-171-243-49-133.ngrok-free.app"
    url_local = "http://localhost:11434"
    try:
        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "top_p": top_p,
        }

        if stop:  # Nếu có danh sách stop words thì thêm vào payload
            payload["stop"] = stop

        async with session.post(f"{url_ngrok}/api/chat", json=payload) as response:
            yield "<think>\n"

            async for chunk in response.content.iter_any():
                try:
                    chunk_data = json.loads(chunk.decode("utf-8"))  # Parse JSON
                    content = chunk_data.get("message", {}).get(
                        "content", ""
                    )  # Lấy nội dung
                    yield content  # Stream nội dung đến client
                    await asyncio.sleep(0.01)
                except json.JSONDecodeError:
                    continue  # Nếu lỗi parse JSON, bỏ qua chunk này

            yield "\n</think>\n\n"

    except aiohttp.ClientError as e:
        yield f"<error>{str(e)}</error>"


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
                        Được rồi, đến với vấn đề: "{prompt}". Lưu ý: Bạn hãy đóng vai là người đang mắc phải vấn đề trên và suy nghĩ theo ngôi thứ nhất:
                            Trước tiên Tôi nên tự hỏi bản thân mình:
                                1. Tôi nên làm gì trong tình huống này?
                                2. Những lợi ích và hạn chế của từng lựa chọn là gì?
                                3. Tôi sẽ làm gì để tối ưu lợi ích cho mình?
                            Sau đó, tôi sẽ chia vấn đề "{prompt}" ra thành từng vấn đề nhỏ và giải quyết chúng.
                    """
                ).strip()
                if contains_code_keywords(prompt):
                    debate_prompt = textwrap.dedent(
                        f"""
                        Được rồi, đến với vấn đề: "{prompt}". Lưu ý: Bạn hãy đóng vai là người đang mắc phải vấn đề trên và suy nghĩ theo ngôi thứ nhất:
                        Trước tiên, tôi cần tự đặt câu hỏi để hiểu rõ hơn về vấn đề:
                            1. Tôi đang gặp lỗi hoặc thách thức gì trong đoạn code này?
                            2. Có những phương án nào để giải quyết, và ưu nhược điểm của từng phương án là gì?
                            3. Giải pháp nào là tối ưu nhất về hiệu suất, bảo trì và khả năng mở rộng?

                        Tiếp theo, tôi sẽ **chia nhỏ vấn đề** thành từng phần cụ thể:
                            - Xác định nguyên nhân gây ra vấn đề (bug, thiết kế chưa tối ưu, hoặc thiếu kiến thức về công nghệ liên quan).
                            - Nếu có lỗi, phân tích **stack trace** hoặc **log** để tìm ra điểm sai.
                            - Nếu là vấn đề về thiết kế, xem xét mô hình **design pattern** hoặc kiến trúc phù hợp hơn.
                            - Nếu liên quan đến hiệu suất, kiểm tra cách tối ưu hoá thuật toán, truy vấn hoặc memory management.

                        Sau khi phân tích xong, tôi sẽ viết ra **giải pháp cụ thể** bằng code (nếu có thể) hoặc hướng dẫn chi tiết để áp dụng.
                        """
                    ).strip()

                brain_think.append({"role": "user", "content": debate_prompt})
                repo.insert_brain_history_chat(
                    chat_ai_id, role="user", content=debate_prompt
                )

                deepthink_response = ""  # Tạo biến chứa toàn bộ kết quả
                async for part in stream_response_deepthink(
                    session, model, brain_think
                ):
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
                search_results = (
                    search_duckduckgo_unlimited(prompt)
                    if contains_search_keywords(prompt)
                    else None
                )
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
            if is_deep_think:
                debate_prompt = textwrap.dedent(
                    f"""
                        Được rồi, đến với vấn đề: "{prompt}". Lưu ý: Bạn hãy đóng vai là người đang mắc phải vấn đề trên và suy nghĩ theo ngôi thứ nhất:
                            Trước tiên Tôi nên tự hỏi bản thân mình:
                                1. Tôi nên làm gì trong tình huống này?
                                2. Những lợi ích và hạn chế của từng lựa chọn là gì?
                                3. Tôi sẽ làm gì để tối ưu lợi ích cho mình?
                            Sau đó, tôi sẽ chia vấn đề "{prompt}" ra thành từng vấn đề nhỏ và giải quyết chúng.
                    """
                ).strip()
                if contains_code_keywords(prompt):
                    debate_prompt = textwrap.dedent(
                        f"""
                        Được rồi, đến với vấn đề: "{prompt}". Lưu ý: Bạn hãy đóng vai là người đang mắc phải vấn đề trên và suy nghĩ theo ngôi thứ nhất:
                        Trước tiên, tôi cần tự đặt câu hỏi để hiểu rõ hơn về vấn đề:
                            1. Tôi đang gặp lỗi hoặc thách thức gì trong đoạn code này?
                            2. Có những phương án nào để giải quyết, và ưu nhược điểm của từng phương án là gì?
                            3. Giải pháp nào là tối ưu nhất về hiệu suất, bảo trì và khả năng mở rộng?

                        Tiếp theo, tôi sẽ **chia nhỏ vấn đề** thành từng phần cụ thể:
                            - Xác định nguyên nhân gây ra vấn đề (bug, thiết kế chưa tối ưu, hoặc thiếu kiến thức về công nghệ liên quan).
                            - Nếu có lỗi, phân tích **stack trace** hoặc **log** để tìm ra điểm sai.
                            - Nếu là vấn đề về thiết kế, xem xét mô hình **design pattern** hoặc kiến trúc phù hợp hơn.
                            - Nếu liên quan đến hiệu suất, kiểm tra cách tối ưu hoá thuật toán, truy vấn hoặc memory management.

                        Sau khi phân tích xong, tôi sẽ viết ra **giải pháp cụ thể** bằng code (nếu có thể) hoặc hướng dẫn chi tiết để áp dụng.
                        """
                    ).strip()

                brain_think.append({"role": "user", "content": debate_prompt})

                deepthink_response = ""  # Tạo biến chứa toàn bộ kết quả
                async for part in stream_response_deepthink(
                    session, model, brain_think
                ):
                    yield part  # Gửi từng phần cho client ngay lập tức
                    deepthink_response += part  # Gom lại toàn bộ câu trả lời

                brain_answer.append(
                    {"role": "assistant", "content": deepthink_response}
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

            elif is_search:
                search_results = (
                    search_duckduckgo_unlimited(prompt)
                    if contains_search_keywords(prompt)
                    else None
                )
                if search_results:
                    extracted_info = extract_search_info(search_results)
                    search = f"""
                        Kết quả tìm kiếm: \n"{extracted_info}"\n Dưa vào kết quả tìm kiếm trên, hãy cung cấp thêm thông tin 'body' và 'href' của website đó.
                    """
                    messages.append({"role": "user", "content": search})

            full_response = ""
            async for part in stream_response_normal(session, model, messages):
                yield part
                full_response += part
            messages.append({"role": "assistant", "content": full_response})

    return StreamingResponse(generate(), media_type="text/plain")


def contains_search_keywords(prompt):
    """
    Kiểm tra xem prompt có chứa các từ ekhóa liên quan đến tìm kiếm không.

    Args:
        prompt (str): Nội dung prompt.

    Returns:
        bool: True nếu prompt chứa từ khóa tìm kiếm, ngược lại False.
    """
    # Danh sách các từ khóa liên quan đến tìm kiếm
    search_keywords = ["tìm kiếm", "search", "tìm", "kiếm", "tra cứu", "hỏi"]

    # Kiểm tra xem prompt có chứa bất kỳ từ khóa nào không
    for keyword in search_keywords:
        if keyword.lower() in prompt.lower():
            return True
    return False


def contains_code_keywords(prompt):
    """
    Kiểm tra xem prompt có chứa các từ khóa liên quan đến lập trình không.

    Args:
        prompt (str): Nội dung prompt.

    Returns:
        bool: True nếu prompt chứa từ khóa lập trình, ngược lại False.
    """
    # Danh sách các từ khóa liên quan đến lập trình và công nghệ
    code_keywords = [
        "code",
        "fix",
        "function",
        "api",
        "bug",
        "debug",
        "stack trace",
        "error",
        "exception",
        "refactor",
        "performance",
        "algorithm",
        "data structure",
        "optimization",
        "git",
        "repository",
        "database",
        "query",
        "memory leak",
        "syntax",
        "deployment",
        "testing",
        "unit test",
        "CI/CD",
        "framework",
        "library",
        "docker",
        "container",
        "cloud",
        "microservice",
        "restful",
        "graphql",
        "backend",
        "frontend",
    ]

    # Kiểm tra xem prompt có chứa bất kỳ từ khóa nào không
    for keyword in code_keywords:
        if keyword.lower() in prompt.lower():
            return True
    return False
