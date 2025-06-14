from datetime import datetime
import json
import aiohttp
import asyncio


async def _process_stream(response, is_type):
    """Xử lý stream từ response, trả về từng chunk đã parse."""
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
                    await asyncio.sleep(0.01)  # Giữ delay nhỏ để tránh overload
                except json.JSONDecodeError as e:
                    print("JSONDecodeError:", e)
        except Exception as e:
            print("Exception in stream processing:", e)

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

        # Gửi request với timeout
        async with session.post(
            f"{url_local}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)  # Timeout 30s
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
        # Gửi request với timeout
        async with session.post(
            f"{url_local}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)  # Timeout 30s
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



########################### DEEPSEARCH ###########################

def analys_question(query):
    prompt = f"""
        Xét câu hỏi: '{query}'.  
        - Nếu câu hỏi không đủ rõ, vô lý, hoặc không thể suy luận (ví dụ: "Mùi của mưa nặng bao nhiêu?"), trả về: "Khó nha bro, [lý do ngắn gọn tự nhiên]."  
        - Nếu câu hỏi có thể suy luận được:  
            1. Tạo keyword: Lấy 2-4 từ khóa chính từ câu hỏi (ngắn gọn, sát nghĩa). * Không cần show ra cho người dùng thấy.  
            2. Phân tích từng keyword: Mỗi từ khóa gợi lên ý gì? Liên quan thế nào đến ý định người dùng?  
            3. Tổng hợp:  
                * Ý định: Người dùng muốn gì? (thông tin, giải pháp, hay gì khác)  
                * Cách hiểu: Câu hỏi có thể diễn giải thế nào?  
            Reasoning và viết ngắn gọn, tự nhiên, không trả lời trực tiếp, ví dụ:  
            'Keyword: [từ khóa 1] - [phân tích], [từ khóa 2] - [phân tích]. Người dùng muốn [ý định], câu này cũng có thể hiểu là [cách hiểu].'  
    """
    return prompt

def better_question(query):
    prompt = f"""
        Câu hỏi gốc: '{query}'  
        Xét kỹ câu hỏi này: Nó thiếu gì để rõ nghĩa hơn? Bổ sung sao cho tự nhiên, cụ thể và dễ hiểu, như cách nói chuyện với bạn. Viết lại thành câu hỏi đầy đủ, giữ ý chính nhưng mạch lạc hơn.  
    """
    return prompt

def analys_prompt(query):
    prompt = f"From the given query, translate it to English if necessary, then provide exactly one concise English search query (no explanations, no extra options) that a user would use to find relevant information on the web. Query: {query}"
    return prompt

def process_link(query, url, content):
    prompt = (
        f"Nội dung từ {url}:\n{content}\n"
        f"Hãy suy luận và trả lời câu hỏi '{query}' dựa trên nội dung được cung cấp, thực hiện theo các bước sau:\n"
        f"* Phân tích nội dung và trích xuất các thông tin quan trọng liên quan đến từ khóa và câu hỏi. Lưu ý các dữ kiện cụ thể (số liệu, sự kiện), bối cảnh, và ý chính. Xem xét cả những chi tiết ngầm hiểu hoặc không được nói trực tiếp.\n"
        f"* Dựa trên thông tin đã phân tích, xây dựng lập luận chi tiết để trả lời câu hỏi. Hãy:\n"
        f"   - So sánh và đối chiếu các dữ kiện nếu có mâu thuẫn hoặc nhiều góc nhìn.\n"
        f"   - Suy ra từ những gì không được nói rõ, nếu nội dung gợi ý điều đó.\n"
        f"   - Đưa ra giả định hợp lý (nếu thiếu dữ liệu) và giải thích tại sao giả định đó có cơ sở.\n"
        f"   - Nếu có thể, dự đoán hoặc mở rộng suy luận để làm rõ thêm ý nghĩa của câu trả lời.\n"
        f"* Viết câu trả lời đầy đủ, tự nhiên, dựa hoàn toàn trên nội dung và suy luận, không thêm thông tin ngoài.\n"
    )   
    return prompt

def reason_with_ollama(query, content):
    prompt = (
        f"Câu hỏi chính: {query}\n"
        f"Thông tin: {content}\n"
        f"Hãy reasoning và trả lời trực tiếp câu hỏi chính '{query}' dựa trên thông tin được cung cấp. Thực hiện theo các bước sau, nhưng không hiển thị số bước hay tiêu đề trong câu trả lời:\n"
        f"- Tìm các dữ kiện quan trọng trong thông tin, bao gồm cả chi tiết cụ thể (số liệu, sự kiện) và ý nghĩa ngầm hiểu nếu có.\n"
        f"- Dựa trên dữ kiện, xây dựng lập luận hợp lý bằng cách liên kết các thông tin với nhau; nếu thiếu dữ liệu, đưa ra suy đoán có cơ sở và giải thích; xem xét các khả năng khác nhau nếu phù hợp, rồi chọn hướng trả lời tốt nhất.\n"
        f"- Cuối cùng, trả lời ngắn gọn, rõ ràng, đúng trọng tâm câu hỏi, dựa hoàn toàn trên lập luận.\n"
        f"Viết tự nhiên, mạch lạc như một đoạn văn liền mạch, chỉ dùng thông tin từ context, không thêm dữ liệu ngoài.\n"
    )  
    return prompt

def evaluate_answer(query, answer, processed_urls):
    prompt = (
        f"Câu trả lời: {answer}\n"
        f"Câu ban đầu: {query}\n"
        f"Danh sách URL đã phân tích: {processed_urls}\n"
        f"Nếu URL này trùng với bất kỳ URL nào trong danh sách đã phân tích, trả lời 'Chưa đủ' và không đánh giá thêm.\n"
        f"Hãy đánh giá xem câu trả lời này đã cung cấp đầy đủ thông tin để giải quyết câu ban đầu chưa. "
        f"- 'Đầy đủ' nghĩa là câu trả lời đáp ứng trực tiếp, rõ ràng và không thiếu khía cạnh quan trọng nào của câu hỏi.\n"
        f"- 'Chưa đủ' nghĩa là còn thiếu thông tin cần thiết hoặc không trả lời đúng trọng tâm.\n"
        f"Trả lời bắt đầu bằng 'Đã đủ' nếu thông tin đầy đủ, hoặc 'Chưa đủ' nếu thiếu thông tin cần thiết.\n"
        f"- Nếu 'Đã đủ', chỉ viết 'Đã đủ', không thêm gì nữa.\n"
        f"- Nếu 'Chưa đủ', thêm phần 'Đề xuất truy vấn:' với CHỈ 1 truy vấn cụ thể bằng tiếng Anh, ngắn gọn, dạng cụm từ tìm kiếm (không phải câu hỏi), liên quan trực tiếp đến câu ban đầu, theo định dạng:\n"
        f"Đề xuất truy vấn:\n* \"từ khóa hoặc cụm từ tìm kiếm cụ thể\"\n"
        f"Ví dụ: Nếu câu ban đầu là 'Làm sao để học tiếng Anh nhanh?' và câu trả lời là 'Học từ vựng mỗi ngày', thì:\n"
        f"Chưa đủ\nĐề xuất truy vấn:\n* \"methods to learn English faster\"\n"
        f"Đảm bảo luôn bắt đầu bằng 'Đã đủ' hoặc 'Chưa đủ', và truy vấn phải là cụm từ tìm kiếm, không phải câu hỏi."
    )
    return prompt

def summarize_answers(query, all_answers):
    prompt = f"""
        Câu hỏi: '{query}'  
        Thông tin thu thập: {'\n'.join([f'- {a}' for a in all_answers])}  
        Trả lời '{query}' bằng cách:  
        - Suy luận từng thông tin: Ý này nói gì? Liên quan thế nào đến câu hỏi? Loại ý không hợp lệ và giải thích ngắn gọn lý do.  
        - Gộp các ý liên quan thành câu trả lời đầy đủ, đúng trọng tâm.  
        - Sắp xếp logic (theo thời gian, mức độ quan trọng, hoặc chủ đề).  
        - Viết đầy đủ, tự nhiên, như nói với bạn, không dùng tiêu đề hay phân đoạn.  
        - Thêm thông tin bổ sung nếu có (URL, file...).  
    """
    return prompt

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
    url_local="http://localhost:11434",
    task_type=None,  # Thay thế các cờ bằng một tham số duy nhất
):
    """Gửi yêu cầu stream đến Ollama API với task_type xác định logic xử lý."""
    try:
        # Dictionary ánh xạ task_type với hàm xử lý prompt
        task_handlers = {
            "analys_question": lambda: analys_question(messages),
            "better_question": lambda: better_question(messages),
            "analys_prompt": lambda: analys_prompt(messages),
            "process_link": lambda: process_link(messages, url, content),
            "reason": lambda: reason_with_ollama(messages, content),
            "evaluate_answer": lambda: evaluate_answer(messages, answer, processed_urls),
            "summarize_answers": lambda: summarize_answers(messages, all_answers),
        }

        # Chọn handler dựa trên task_type, mặc định raise lỗi nếu không hợp lệ
        if task_type not in task_handlers:
            raise ValueError(f"Task type '{task_type}' không hợp lệ. Chọn: {list(task_handlers.keys())}")
        prompt = task_handlers[task_type]()

        # Chuẩn bị payload
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

        # Gửi request với timeout
        async with session.post(
            f"{url_local}/api/chat",
            json=payload,
            timeout=aiohttp.ClientTimeout(total=30)  # Timeout 30s
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
        

# Hàm test mẫu# Hàm test chạy lần lượt các task_type
async def test_stream_response_deepsearch():
    # Danh sách tất cả task_type
    task_types = [
        "analys_question",
        "analys_prompt",
        "process_link",
        "reason",
        "evaluate_answer",
        "summarize_answers"
    ]

    # Input mẫu
    messages = [{"role": "user", "content": "Lên kế hoạch đi Đà Lạt 3 ngày 2 đêm"}]
    model = "gemma3"
    max_tokens = 200

    async with aiohttp.ClientSession() as session:
        for task_type in task_types:
            print(f"\n=== Chạy task_type: {task_type} ===")
            stream = stream_response_deepsearch(
                session=session,
                messages=messages,
                task_type=task_type,
                url="http://example.com",  # Thêm giá trị mẫu cho các tham số khác
                content="Nội dung mẫu từ link",
                processed_urls="http://example.com, http://test.com",
                all_answers="Câu trả lời 1, Câu trả lời 2",
                model=model,
                max_tokens=max_tokens,
            )
            
            full_response = ""
            async for chunk in stream:
                # print("Chunk:", chunk.strip())  # Uncomment nếu muốn xem chi tiết từng chunk
                chunk_data = json.loads(chunk)
                if chunk_data.get("type") == "deepsearch":
                    full_response += chunk_data["message"]["content"]
            print("Full response:", full_response)

if __name__ == "__main__":
    asyncio.run(test_stream_response_deepsearch())