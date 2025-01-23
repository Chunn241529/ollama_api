import os
import shutil
import flet as ft
from openai import OpenAI
from components.chat.header import create_header
from components.chat.chat import create_chat
from components.chat.test1 import create_input_area
import json

# Cấu hình API key của OpenAI (thay thế bằng API key thực)
client = OpenAI(base_url=f"http://localhost:11434/v1", api_key="ollama")
messages = []
selected_image = None
model = "llama3.2:3b"


def delete_pycache(root_dir):
    for dirpath, dirnames, _ in os.walk(root_dir):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"Deleted: {pycache_path}")


# Xóa thư mục __pycache__
delete_pycache(os.getcwd())


def load_data():
    try:
        with open("data.json", "r") as file:
            data = json.load(file)
            return data
    except FileNotFoundError:
        return {}


def save_data(data):
    with open("data.json", "w") as file:
        json.dump(data, file)


def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.LIGHT
    page.title = "ChunGPT"
    page.horizontal_alignment = "center"
    page.padding = 10

    # Thêm sự kiện on_tap cho page

    # Điều chỉnh kích thước cửa sổ dựa trên kích thước màn hình
    if page.width < 600:  # Nếu màn hình nhỏ hơn 600px (điện thoại)
        page.window_width = 400
        page.window_height = 800
    else:  # Nếu màn hình lớn hơn hoặc bằng 600px (máy tính)
        page.window_width = 1280
        page.window_height = 720

    # Tạo FilePicker
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # Tạo các component
    header = create_header()
    chat = create_chat()
    input_area = create_input_area(file_picker, chat, page, client, model)

    # Lấy dữ liệu từ tệp tin JSON
    data = load_data()

    # Tạo giao diện
    page.add(
        ft.Column(
            [
                header,
                chat,
                ft.Row(
                    [input_area],
                    alignment=ft.MainAxisAlignment.CENTER,
                    width=(
                        700 if page.window.width > 600 else "100%"
                    ),  # Đặt width thành 100% để responsive  # Đặt width thành 100% để responsive
                ),
            ],
            expand=True,
            width=(
                700 if page.window.width > 600 else "100%"
            ),  # Đặt width thành 100% để responsive
        )
    )


# Chạy ứng dụng
ft.app(target=main)
