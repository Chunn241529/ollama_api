# main.py
import os
import shutil
import flet as ft
from openai import OpenAI
from components.authentication.login import create_login_page
from components.authentication.register import create_register_page
from components.chat.header import create_header
from components.chat.chat import create_chat
from components.chat.test1 import create_input_area

# Cấu hình API key của OpenAI (thay thế bằng API key thực)
client = OpenAI(base_url=f"http://localhost:11434/v1", api_key="ollama")
messages = []
selected_image = None
model = "chunn1.0:latest"  # Model mặc định


# Xóa thư mục __pycache__
def delete_pycache(root_dir):
    for dirpath, dirnames, _ in os.walk(root_dir):
        if "__pycache__" in dirnames:
            pycache_path = os.path.join(dirpath, "__pycache__")
            shutil.rmtree(pycache_path)
            print(f"Deleted: {pycache_path}")


delete_pycache(os.getcwd())


# Tạo giao diện dashboard (ChunGPT)
def create_dashboard_page(page):
    # Tạo FilePicker
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    # Biến toàn cục để lưu giá trị model
    global model

    # Tham chiếu đến input_area để cập nhật khi model thay đổi
    input_area_ref = ft.Ref[ft.Column]()

    def update_model(new_model):
        # Cập nhật giá trị model
        global model
        model = new_model
        print(f"Model đã được cập nhật thành: {model}")

        # Cập nhật lại input_area với model mới
        input_area_ref.current.controls = [
            create_input_area(file_picker, chat, page, client, model)
        ]
        input_area_ref.current.update()

    # Tạo các component
    header = create_header(update_model)
    chat = create_chat()
    input_area = create_input_area(file_picker, chat, page, client, model, chat_id=1)

    return ft.Column(
        [
            header,
            chat,
            ft.Row(
                ref=input_area_ref,
                controls=[input_area],
                alignment=ft.MainAxisAlignment.CENTER,
                width=(700 if page.window.width > 600 else "100%"),
            ),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        expand=True,
        width=(700 if page.window.width > 600 else "100%"),
    )


# Hàm chính
def main(page: ft.Page):
    page.theme_mode = ft.ThemeMode.DARK
    page.title = "ChunGPT"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.padding = 10

    # Điều chỉnh kích thước cửa sổ dựa trên kích thước màn hình
    if page.width < 600:  # Nếu màn hình nhỏ hơn 600px (điện thoại)
        page.window_width = 400
        page.window_height = 800
    else:  # Nếu màn hình lớn hơn hoặc bằng 600px (máy tính)
        page.window_width = 500
        page.window_height = 700

    def route_change(route):
        page.views.clear()
        if page.route == "/login":
            # Căn giữa trang đăng nhập
            login_page = ft.Column(
                [create_login_page(page)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )
            page.views.append(ft.View("/login", [login_page]))
        elif page.route == "/register":
            # Căn giữa trang đăng ký
            register_page = ft.Column(
                [create_register_page(page)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )
            page.views.append(ft.View("/register", [register_page]))
        elif page.route == "/chat":
            # Căn giữa trang chat (dashboard)
            chat_page = ft.Column(
                [create_dashboard_page(page)],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                expand=True,
            )
            page.views.append(ft.View("/chat", [chat_page]))
        page.update()

    page.on_route_change = route_change
    page.go("/login")  # Mặc định mở trang đăng nhập


# Chạy ứng dụng
ft.app(target=main)
