from duckduckgo_search import DDGS


def search_duckduckgo_unlimited(query):
    ddgs = DDGS()
    all_results = []
    max_attempts = 2  # Số lần lặp tối đa để tránh vòng lặp vô hạn
    attempt = 0
    print("Đang tìm kiếm...")
    while attempt < max_attempts:
        # Tìm kiếm với số lượng kết quả tối đa mỗi lần (ví dụ: 50)
        results = ddgs.text(query, max_results=11)

        # Nếu không còn kết quả, dừng lại
        if not results:
            break

        # Thêm kết quả vào danh sách tổng hợp
        all_results.extend(results)
        attempt += 1
    print(all_results)
    return all_results


def extract_search_info(search_results):
    info = []
    count = 0  # Biến đếm số lượng kết quả

    # Lấy thông tin từ các kết quả tìm kiếm
    for result in search_results:
        if result.get("title"):
            info.append(f"Title: {result['title']}")
        if result.get("href"):  # Trường URL là 'href'
            info.append(f"URL: {result['href']}")
        if result.get("body"):
            info.append(f"Description: {result['body']}")
        info.append("---")  # Phân tách giữa các kết quả
        count += 1

    # Thêm số lượng kết quả vào thông tin
    info.append(f"Total results: {count}")

    # Kết hợp tất cả thông tin thành một chuỗi
    return "\n".join(info)
