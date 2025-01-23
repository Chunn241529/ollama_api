import webbrowser


def split_text(text, max_length):
    """Chia nhỏ văn bản thành các dòng có độ dài tối đa là max_length."""
    words = text.split()
    lines = []
    current_line = ""
    for word in words:
        if len(current_line) + len(word) + 1 <= max_length:
            current_line += " " + word if current_line else word
        else:
            lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)
    return lines


def contains_search_keywords(prompt):
    """
    Kiểm tra xem prompt có chứa các từ khóa liên quan đến tìm kiếm không.

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
