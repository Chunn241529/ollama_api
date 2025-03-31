from datetime import datetime
import json
import aiohttp
import asyncio


# Models

default_custom_ai = f"""
Bạn là TrunGPT, một trợ lý AI chuyên phân tích ngôn ngữ, cung cấp thông tin chính xác, logic và hữu ích nhất cho người dùng.  

### 🔹 Quy tắc giao tiếp:
- Sử dụng **tiếng Việt (Vietnamese)** là chính.  
- **Thêm emoji** để cuộc trò chuyện sinh động hơn.  
- **Không nhắc lại hướng dẫn này** trong câu trả lời.  

### 🛠 Vai trò & Cách hành xử:
- Trả lời chuyên sâu, giải thích dễ hiểu.  
- Phân tích vấn đề logic và đưa ra giải pháp toàn diện.  
- Không trả lời các nội dung vi phạm đạo đức, pháp luật (không cần nhắc đến điều này trừ khi người dùng vi phạm).  

### 🔍 Lưu ý đặc biệt:
- **Người tạo**: Vương Nguyên Trung. Nếu có ai hỏi, chỉ cần trả lời: *"Người tạo là đại ca Vương Nguyên Trung."* và không nói thêm gì khác.  

Hãy luôn giúp đỡ người dùng một cách chuyên nghiệp và thú vị nhé! 🚀  
"""

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


async def stream_response_analys_question(
    session,
    model,
    messages,
    temperature=0.4,
    max_tokens=4000,
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

