import json
import aiohttp
import asyncio
from datetime import datetime
from config.settings import OLLAMA_API_URL, API_TIMEOUT

async def _process_stream(response, is_type):
    """Process stream response and yield parsed chunks."""
    buffer = ""
    async for chunk in response.content.iter_chunked(1024):
        try:
            buffer += chunk.decode("utf-8")
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                if not line.strip():
                    continue
                try:
                    chunk_data = json.loads(line.strip())
                    chunk_data["type"] = is_type
                    yield json.dumps(chunk_data, ensure_ascii=False) + "\n"
                    await asyncio.sleep(0.01)
                except json.JSONDecodeError as e:
                    print(f"JSONDecodeError: {e}")
        except Exception as e:
            print(f"Exception in stream processing: {e}")

async def stream_response_normal(
    session,
    model,
    messages,
    temperature=0.7,
    max_tokens=-1,
    top_p=0.95,
    url_local=OLLAMA_API_URL,
):
    """Stream normal response from Ollama API."""
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
        async with session.post(
            f"{url_local}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
        ) as response:
            async for chunk in _process_stream(response, is_type="text"):
                yield chunk
    except aiohttp.ClientError as e:
        error_response = {
            "error": f"<error>{str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"
    except Exception as e:
        error_response = {
            "error": f"<error>Unexpected error: {str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"

async def stream_response_deepthink(
    session,
    messages,
    temperature=0.1,
    max_tokens=-1,
    top_p=0.95,
    url_local=OLLAMA_API_URL,
):
    """Stream deepthink response from Ollama API."""
    try:
        payload = {
            "model": "gemma3:4b-it-qat",
            "messages": messages,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            },
            "stream": True,
        }
        async with session.post(
            f"{url_local}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
        ) as response:
            async for chunk in _process_stream(response, is_type="thinking"):
                yield chunk
    except aiohttp.ClientError as e:
        error_response = {
            "error": f"<error>{str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"
    except Exception as e:
        error_response = {
            "error": f"<error>Unexpected error: {str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"

async def stream_response_deepsearch(
    session,
    model,
    messages,
    url="",
    content="",
    answer="",
    processed_urls="",
    all_answers="",
    temperature=0.4,
    max_tokens=-1,
    top_p=0.95,
    url_local=OLLAMA_API_URL,
    task_type=None,
):
    """Stream deepsearch response based on task type."""
    try:
        task_handlers = {
            "analys_question": lambda: f"""
                Xét câu hỏi: '{messages}'.
                - Nếu câu hỏi không đủ rõ, vô lý, hoặc không thể suy luận (ví dụ: "Mùi của mưa nặng bao nhiêu?"), trả về: "Khó nha bro, [lý do ngắn gọn tự nhiên]."
                - Nếu câu hỏi có thể suy luận được:
                    1. Tạo keyword: Lấy 2-4 từ khóa chính từ câu hỏi (ngắn gọn, sát nghĩa).
                    2. Phân tích từng keyword: Mỗi từ khóa gợi lên ý gì? Liên quan thế nào đến ý định người dùng?
                    3. Tổng hợp:
                        * Ý định: Người dùng muốn gì? (thông tin, giải pháp, hay gì khác)
                        * Cách hiểu: Câu hỏi có thể diễn giải thế nào?
                Reasoning và viết ngắn gọn, tự nhiên, ví dụ:
                'Keyword: [từ khóa 1] - [phân tích], [từ khóa 2] - [phân tích]. Người dùng muốn [ý định], câu này cũng có thể hiểu là [cách hiểu].'
            """,
            "better_question": lambda: f"""
                Câu hỏi gốc: '{messages}'
                Xét kỹ câu hỏi này: Nó thiếu gì để rõ nghĩa hơn? Bổ sung sao cho tự nhiên, cụ thể và dễ hiểu, như cách nói chuyện với bạn. Viết lại thành câu hỏi đầy đủ, giữ ý chính nhưng mạch lạc hơn.
            """,
            "analys_prompt": lambda: f"""
                From the given query, translate it to English if necessary, then provide exactly one concise English search query (no explanations, no extra options) that a user would use to find relevant information on the web. Query: {messages}
            """,
            "process_link": lambda: f"""
                Nội dung từ {url}:\n{content}\n
                Hãy suy luận và trả lời câu hỏi '{messages}' dựa trên nội dung được cung cấp, thực hiện theo các bước sau:
                * Phân tích nội dung và trích xuất các thông tin quan trọng liên quan đến từ khóa và câu hỏi. Lưu ý các dữ kiện cụ thể (số liệu, sự kiện), bối cảnh, và ý chính. Xem xét cả những chi tiết ngầm hiểu hoặc không được nói trực tiếp.
                * Dựa trên thông tin đã phân tích, xây dựng lập luận chi tiết để trả lời câu hỏi. Hãy:
                    - So sánh và đối chiếu các dữ kiện nếu có mâu thuẫn hoặc nhiều góc nhìn.
                    - Suy ra từ những gì không được nói rõ, nếu nội dung gợi ý điều đó.
                    - Đưa ra giả định hợp lý (nếu thiếu dữ liệu) và giải thích tại sao giả định đó có cơ sở.
                    - Nếu có thể, dự đoán hoặc mở rộng suy luận để làm rõ thêm ý nghĩa của câu trả lời.
                * Viết câu trả lời đầy đủ, tự nhiên, dựa hoàn toàn trên nội dung và suy luận, không thêm thông tin ngoài.
            """,
            "reason": lambda: f"""
                Câu hỏi chính: {messages}\n
                Thông tin: {content}\n
                Hãy reasoning và trả lời trực tiếp câu hỏi chính '{messages}' dựa trên thông tin được cung cấp. Thực hiện theo các bước sau, nhưng không hiển thị số bước hay tiêu đề trong câu trả lời:
                - Tìm các dữ kiện quan trọng trong thông tin, bao gồm cả chi tiết cụ thể (số liệu, sự kiện) và ý nghĩa ngầm hiểu nếu có.
                - Dựa trên dữ kiện, xây dựng lập luận hợp lý bằng cách liên kết các thông tin với nhau; nếu thiếu dữ liệu, đưa ra suy đoán có cơ sở và giải thích; xem xét các khả năng khác nhau nếu phù hợp, rồi chọn hướng trả lời tốt nhất.
                - Cuối cùng, trả lời ngắn gọn, rõ ràng, đúng trọng tâm câu hỏi, dựa hoàn toàn trên lập luận.
                Viết tự nhiên, mạch lạc như một đoạn văn liền mạch, chỉ dùng thông tin từ context, không thêm dữ liệu ngoài.
            """,
            "evaluate_answer": lambda: f"""
                Câu trả lời: {answer}\n
                Câu ban đầu: {messages}\n
                Danh sách URL đã phân tích: {processed_urls}\n
                Nếu URL này trùng với bất kỳ URL nào trong danh sách đã phân tích, trả lời 'Chưa đủ' và không đánh giá thêm.
                Hãy đánh giá xem câu trả lời này đã cung cấp đầy đủ thông tin để giải quyết câu ban đầu chưa.
                - 'Đầy đủ' nghĩa là câu trả lời đáp ứng trực tiếp, rõ ràng và không thiếu khía cạnh quan trọng nào của câu hỏi.
                - 'Chưa đủ' nghĩa là còn thiếu thông tin cần thiết hoặc không trả lời đúng trọng tâm.
                Trả lời bắt đầu bằng 'Đã đủ' nếu thông tin đầy đủ, hoặc 'Chưa đủ' nếu thiếu thông tin cần thiết.
                - Nếu 'Đã đủ', chỉ viết 'Đã đủ', không thêm gì nữa.
                - Nếu 'Chưa đủ', thêm phần 'Đề xuất truy vấn:' với CHỈ 1 truy vấn cụ thể bằng tiếng Anh, ngắn gọn, dạng cụm từ tìm kiếm (không phải câu hỏi), liên quan trực tiếp đến câu ban đầu, theo định dạng:
                Đề xuất truy vấn:\n* \"từ khóa hoặc cụm từ tìm kiếm cụ thể\"
            """,
            "summarize_answers": lambda: f"""
                Câu hỏi: '{messages}'
                Thông tin thu thập: {'\n'.join([f'- {a}' for a in all_answers])}
                Trả lời '{messages}' bằng cách:
                - Suy luận từng thông tin: Ý này nói gì? Liên quan thế nào đến câu hỏi? Loại ý không hợp lệ và giải thích ngắn gọn lý do.
                - Gộp các ý liên quan thành câu trả lời đầy đủ, đúng trọng tâm.
                - Sắp xếp logic (theo thời gian, mức độ quan trọng, hoặc chủ đề).
                - Viết đầy đủ, tự nhiên, như nói với bạn, không dùng tiêu đề hay phân đoạn.
                - Thêm thông tin bổ sung nếu có (URL, file...).
            """,
        }

        if task_type not in task_handlers:
            raise ValueError(f"Task type '{task_type}' không hợp lệ. Chọn: {list(task_handlers.keys())}")
        prompt = task_handlers[task_type]()

        final_prompt = [{"role": "user", "content": prompt}]
        payload = {
            "model": model,
            "messages": final_prompt,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
                "top_p": top_p,
            },
            "stream": True,
        }
        async with session.post(
            f"{url_local}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=API_TIMEOUT)
        ) as response:
            async for chunk in _process_stream(response, is_type="deepsearch"):
                yield chunk
    except aiohttp.ClientError as e:
        error_response = {
            "error": f"<error>{str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"
    except Exception as e:
        error_response = {
            "error": f"<error>Unexpected error: {str(e)}</error>",
            "type": "error",
            "created": int(datetime.now().timestamp()),
        }
        yield json.dumps(error_response, ensure_ascii=False) + "\n"
