import subprocess
import textwrap
import json
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import aiohttp
from models.chat import ChatRequest, ManagerChat
from dependencies.auth import verify_token, call_api_get_dbname
from services.generate import stream_response_normal, stream_response_deepthink, stream_response_deepsearch
from services.repository.repo_client import RepositoryClient
from services.func.search import extract_search_info, search_duckduckgo_unlimited
from config.settings import DEFAULT_CUSTOM_AI, DEFAULT_THINK_AI
from services.deepsearch import deepsearch  # Import deepsearch function

router = APIRouter(prefix="/chat", tags=["chat"])

# Other functions (get_available_models, models, models_test, create_chat, get_chat, get_history_chat) remain unchanged

@router.post("/send")
async def chat(chat_request: ChatRequest, current_user: dict = Depends(verify_token)):
    """Send chat request to Ollama API and stream response."""
    prompt = chat_request.prompt
    model = chat_request.model
    chat_ai_id = chat_request.chat_ai_id
    is_deep_think = chat_request.is_deep_think
    is_search = chat_request.is_search
    is_deepsearch = chat_request.is_deepsearch  # Add is_deepsearch check

    username = current_user["username"]
    db_path = await call_api_get_dbname(username)
    repo = RepositoryClient(db_path)
    custom_ai = repo.get_custom_chat_ai_by_id(chat_ai_id)
    custom_ai_text = custom_ai[0]

    history_chat = repo.get_brain_history_chat_by_chat_ai_id(chat_ai_id)
    messages = [{"role": "system", "content": custom_ai_text}]
    for role, content in history_chat:
        messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": prompt})
    repo.insert_brain_history_chat(chat_ai_id, role="user", content=prompt)

    async def generate():
        async with aiohttp.ClientSession() as session:
            if is_deep_think:
                debate_prompt = textwrap.dedent(
                    """
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
                brain_think = [{"role": "user", "content": debate_prompt}]
                repo.insert_brain_history_chat(chat_ai_id, role="user", content=debate_prompt)

                deepthink_response = ""
                async for part in stream_response_deepthink(session, brain_think):
                    yield part
                    chunk_data = json.loads(part)
                    deepthink_response += chunk_data["message"]["content"]

                repo.insert_brain_history_chat(chat_ai_id, role="assistant", content=deepthink_response)
                refined_prompt = textwrap.dedent(
                    f"""
                    Dựa trên phân tích "{deepthink_response}", hãy đưa ra kết luận cuối cùng cho câu hỏi: "{prompt}" đầy đủ và logic nhất.
                    """
                ).strip()
                messages.append({"role": "user", "content": refined_prompt})
                repo.insert_brain_history_chat(chat_ai_id, role="user", content=refined_prompt)

            elif is_search:
                search_results = search_duckduckgo_unlimited(prompt)
                if search_results:
                    extracted_info = extract_search_info(search_results)
                    search = f"""
                        Kết quả tìm kiếm: \n"{extracted_info}"\n Dưa vào kết quả tìm kiếm trên, hãy cung cấp thêm thông tin 'body' và 'href' của website đó.
                    """
                    messages.append({"role": "user", "content": search})
                    repo.insert_brain_history_chat(chat_ai_id, role="user", content=search)

            elif is_deepsearch:
                full_response = ""
                async for chunk in deepsearch(messages, session=session, model=model):
                    yield chunk
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("type") == "deepsearch":
                        full_response += chunk_data["message"]["content"]
                messages.append({"role": "assistant", "content": full_response})
                repo.insert_brain_history_chat(chat_ai_id, role="assistant", content=full_response)

            else:
                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    chunk_data = json.loads(part)
                    full_response += chunk_data["message"]["content"]
                messages.append({"role": "assistant", "content": full_response})
                repo.insert_brain_history_chat(chat_ai_id, role="assistant", content=full_response)

    return StreamingResponse(generate(), media_type="text/plain")

@router.post("/test")
async def chat_test(chat_request: ChatRequest):
    """Test chat endpoint without authentication."""
    prompt = chat_request.prompt
    model = chat_request.model
    is_deep_think = chat_request.is_deep_think
    is_deepsearch = chat_request.is_deepsearch

    messages = [{"role": "system", "content": DEFAULT_CUSTOM_AI}]
    messages.append({"role": "user", "content": prompt})

    async def generate():
        async with aiohttp.ClientSession() as session:
            if is_deep_think:
                brain_think = [{"role": "system", "content": DEFAULT_THINK_AI}, {"role": "user", "content": prompt}]
                deepthink_response = ""
                async for part in stream_response_deepthink(session, brain_think):
                    yield part
                    chunk_data = json.loads(part)
                    deepthink_response += chunk_data["message"]["content"]

                refined_prompt = f"""
                Hãy xem lại suy nghĩ của bạn: "{deepthink_response}".
                Giờ, trả lời câu hỏi "{prompt}" một cách rõ ràng và tự nhiên nhất, như đang trò chuyện với một người bạn.
                - Tập trung vào ý chính, giải thích dễ hiểu, tránh dùng từ ngữ quá phức tạp.
                - Tổng hợp các điểm quan trọng từ suy nghĩ trước để đưa ra câu trả lời logic và đầy đủ.
                """
                messages.append({"role": "user", "content": refined_prompt})

                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    chunk_data = json.loads(part)
                    full_response += chunk_data["message"]["content"]
                messages.append({"role": "assistant", "content": full_response})

            elif is_deepsearch:
                full_response = ""
                async for chunk in deepsearch(messages, session=session, model=model):
                    yield chunk
                    chunk_data = json.loads(chunk)
                    if chunk_data.get("type") == "deepsearch":
                        full_response += chunk_data["message"]["content"]
                messages.append({"role": "assistant", "content": full_response})

            else:
                full_response = ""
                async for part in stream_response_normal(session, model, messages):
                    yield part
                    chunk_data = json.loads(part)
                    full_response += chunk_data["message"]["content"]
                messages.append({"role": "assistant", "content": full_response})

    return StreamingResponse(generate(), media_type="text/plain")
