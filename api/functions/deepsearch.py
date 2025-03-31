
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from datetime import datetime

import requests
import json


# from api.functions.generate import *

from generate import *

history_analys = []


import random                                                                  
                                                                            
def random_number(min, max):                                                           
    """                                                                          
    Hàm này tạo ra một số ngẫu nhiên từ 10 đến 25.                               
    """                                                                          
    return random.randint(min, max)     

max_results = random_number(10, 25) # number of ressults 

# Các hàm từ search.py
def search_web(query, max_results=max_results):
    results = []
    with DDGS() as ddgs:
        for r in ddgs.text(query, max_results=max_results):
            results.append({
                'title': r['title'],
                'url': r['href'],
                'snippet': r['body']
            })
    return results

def extract_content(url, snippet=""):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Kiểm tra lỗi HTTP
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Danh sách các thẻ muốn trích xuất nội dung
        tags_to_extract = ['p', 'h1', 'h2', 'li', 'a']
        content_parts = []
        
        # Duyệt qua từng loại thẻ
        for tag in soup.find_all(tags_to_extract):
            if tag.name == 'a' and tag.get('href'):  # Đặc biệt xử lý thẻ <a>
                text = tag.get_text(strip=True)
                href = tag['href']
                content_parts.append(f"{text} (link: {href})")
            else:  # Các thẻ khác chỉ lấy text
                text = tag.get_text(strip=True)
                if text:  # Chỉ thêm nếu có nội dung
                    content_parts.append(text)
        
        # Ghép tất cả nội dung thành một chuỗi, thêm snippet nếu có
        content = f"Snippet: {snippet}\n" + " ".join(content_parts)
        return content[:5000]  # Giới hạn 5000 ký tự
    
    except requests.RequestException as e:
        return f"Error fetching {url}: {str(e)}"


def extract_queries(text, history_queries=None):
    if history_queries is None:
        history_queries = set()
    # Nếu text không hỗ trợ split(), nghĩa là nó không phải là chuỗi, ta sẽ tiêu thụ nó
    try:
        lines = text.split('\n')
    except AttributeError:
        # Nếu text là generator, chuyển nó thành chuỗi
        text = ''.join(text)
        lines = text.split('\n')

    queries = set()
    in_query_section = False

    for i, line in enumerate(lines):
        line_clean = line.strip().lower()
        if line_clean.startswith('đề xuất truy vấn:') or line_clean.startswith('**đề xuất truy vấn:**'):
            in_query_section = True
        elif in_query_section and (not line.strip() or not line.strip().startswith('*')):
            in_query_section = False

        if in_query_section:
            # Nếu dòng hiện tại không bắt đầu bằng '*' nhưng có chứa 'Đề xuất truy vấn:'
            if i + 1 < len(lines) and not lines[i].strip().startswith('*') and lines[i].strip().startswith('Đề xuất truy vấn:'):
                next_line = lines[i + 1].strip()
                if next_line and not next_line.startswith('Truy vấn từ') and not next_line.startswith('Đánh giá:'):
                    clean_query = next_line.strip('"').strip('*').strip()
                    if clean_query and clean_query not in history_queries:
                        queries.add(clean_query)
            # Nếu dòng hiện tại bắt đầu bằng '*' thì trích xuất phần sau dấu *
            elif line.strip().startswith('*'):
                clean_query = line.strip()[1:].strip().strip('"').strip()
                if clean_query and clean_query not in history_queries:
                    queries.add(clean_query)

    return list(queries)[:1]


async def deepsearch(initial_query, max_iterations=random_number(2, 5), session=None, model="gemma3"):
    if not isinstance(session, aiohttp.ClientSession):
        raise ValueError("Tham số 'session' phải là aiohttp.ClientSession")

    if isinstance(initial_query, list) and initial_query and "content" in initial_query[0]:
        query_str = initial_query[0]["content"]
    else:
        query_str = str(initial_query)

    current_queries = []
    accumulated_context = ""
    all_answers = {}
    all_data = ""
    history_queries = {query_str}
    history_analys = []

    iteration = 0
    processed_urls = set()

    ### Phân tích câu hỏi
    full_analys_question = ""
    async for part in stream_response_deepsearch(session=session, model=model, messages=initial_query, task_type="analys_question"):
        chunk_data = json.loads(part)
        yield part
        full_analys_question += chunk_data["message"]["content"]

    if "Khó nha bro" in full_analys_question:
        all_answers.clear()
        history_analys.clear()

        new_question = ""
        async for part in stream_response_deepsearch(session=session, model=model, messages=initial_query, task_type="better_question"):
            chunk_data = json.loads(part)
            yield part
            new_question += chunk_data["message"]["content"]

        full_analys_question = new_question

    history_analys.append(full_analys_question)

    ### Phân tích tìm kiếm tạo câu truy vấn
    full_analys_prompt = ""
    async for part in stream_response_deepsearch(session=session, model=model, messages=history_analys, task_type="analys_prompt"):
        chunk_data = json.loads(part)
        yield part
        full_analys_prompt += chunk_data["message"]["content"]
    final_analys_prompt = full_analys_prompt.strip('"')
    current_queries.append(final_analys_prompt)  # Đây là chuỗi thô

    while iteration < max_iterations and current_queries:
        current_query = current_queries.pop(0)  # current_query giờ là chuỗi

        yield json.dumps({
            "model": model,
            "created_at": datetime.now().isoformat() + "Z",
            "message": {"role": "assistant", "content": f"Tìm kiếm: {current_query}"},
            "done": False,
            "type": "deepsearch"
        }, ensure_ascii=False) + "\n"

        search_results = search_web(current_query)  # Truyền chuỗi vào search_web
        yield json.dumps({
            "model": model,
            "created_at": datetime.now().isoformat() + "Z",
            "message": {"role": "assistant", "content": f"Tìm thấy {len(search_results)} kết quả."},
            "done": False,
            "type": "deepsearch"
        }, ensure_ascii=False) + "\n"

        if not search_results or any(result.get('title', '').startswith('EOF') for result in search_results):
            all_answers.clear()
            yield json.dumps({
                "model": model,
                "created_at": datetime.now().isoformat() + "Z",
                "message": {"role": "assistant", "content": "Khó nha bro! Không tìm thấy thông tin, để tôi phân tích lại..."},
                "done": False,
                "type": "deepsearch"
            }, ensure_ascii=False) + "\n"
            return

        new_query_found = False
        result_processed = False

        for result in search_results:
            url = result['url']
            if url in processed_urls:
                continue

            content = extract_content(url)
            if "Error" in content:
                continue

            final_analysis = ""
            async for part in stream_response_deepsearch(session=session, model=model, messages=history_analys, url=url, content=content, task_type="process_link"):
                chunk_data = json.loads(part)
                yield part
                final_analysis += chunk_data["message"]["content"]

            sufficiency_prompt = (
                f"Url: {url}\nNội dung phân tích: {final_analysis}\nCâu hỏi ban đầu: {query_str}\n"
                f"Danh sách URL đã phân tích: {', '.join(processed_urls)}\n"
                f"Nếu URL trùng, trả 'NOT YET'. Nếu không, đánh giá đủ chưa: 'OK' nếu đủ, 'NOT YET' nếu chưa, kèm lý do."
            )

            sufficiency_result = ""
            async for part in stream_response_deepsearch(session=session, model=model, messages=history_analys, url=url, content=sufficiency_prompt, task_type="process_link"):
                chunk_data = json.loads(part)
                yield part
                sufficiency_result += chunk_data["message"]["content"]

            if "OK" in sufficiency_result.upper():
                result_processed = True
                all_answers[query_str] = final_analysis
                history_analys.append(final_analysis)
                all_data += f"{url}: {final_analysis}\n"
                processed_urls.add(url)
            elif "NOT YET" not in sufficiency_result.upper():
                result_processed = False
                processed_urls.add(url)
            else:
                result_processed = False
                processed_urls.add(url)

            new_queries = extract_queries(final_analysis, history_queries)
            if new_queries:
                for query in new_queries:
                    if query not in history_queries:
                        current_queries.append(query)  # Thêm chuỗi thô
                        history_queries.add(query)
                        new_query_found = True

            accumulated_context += f"\nNguồn: {url}\n{content}\n"
            if result_processed or new_query_found:
                break

        full_answer = ""
        async for part in stream_response_deepsearch(session=session, model=model, messages=initial_query, content=accumulated_context, task_type="reason"):
            chunk_data = json.loads(part)
            yield part
            full_answer += chunk_data["message"]["content"]
        all_answers[current_query] = full_answer
        history_analys.append(full_answer)

        new_queries_from_reasoning = extract_queries(full_answer)

        full_evaluation = ""
        async for part in stream_response_deepsearch(session=session, model=model, messages=initial_query, content=full_answer, processed_urls=processed_urls, task_type="evaluate_answer"):
            chunk_data = json.loads(part)
            yield part
            full_evaluation += chunk_data["message"]["content"]

        if "đã đủ" in full_evaluation.lower():
            break
        elif "chưa đủ" in full_evaluation.lower() or new_queries_from_reasoning:
            new_queries = extract_queries(full_evaluation) or new_queries_from_reasoning
            relevant_query = new_queries[0] if new_queries else None
            if relevant_query and relevant_query not in current_queries and relevant_query not in all_answers:
                current_queries.append(relevant_query)  # Thêm chuỗi thô
            iteration += 1
        else:
            iteration += 1

    yield json.dumps({
        "model": model,
        "created_at": datetime.now().isoformat() + "Z",
        "message": {"role": "assistant", "content": f"Kết thúc DeepSearch! 🌟\n"},
        "done": False,
        "type": "deepsearch"
    }, ensure_ascii=False) + "\n"

    final_answer = ""
    async for part in stream_response_deepsearch(session=session, model=model, messages=initial_query, content=history_analys, task_type="summarize_answers"):
        chunk_data = json.loads(part)
        yield part
        final_answer += chunk_data["message"]["content"]

    history_analys.clear()
    history_queries.clear()
    all_answers.clear()
                                                           
                                                                                                  
                                                                                                                       
                                                            
                     
# Test với FastAPI hoặc gọi trực tiếp
async def test():
    async with aiohttp.ClientSession() as session:
        full_response = ""  # Khai báo trước vòng lặp
        async for chunk in deepsearch([{"role": "user", "content": "Lên kế hoạch đi Đà Lạt 3 ngày 2 đêm với ngân sách 500k VNĐ"}], session=session, model="gemma3"):
            chunk_data = json.loads(chunk)
            if chunk_data.get("type") == "deepsearch":
                full_response += chunk_data["message"]["content"]
            # print("Full response (streaming):", full_response)  # In từng bước
        print("\nFinal full response:", full_response)  # In kết quả cuối cùng

if __name__ == "__main__":
    asyncio.run(test())