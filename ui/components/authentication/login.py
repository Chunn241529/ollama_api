# login.py
import flet as ft
import requests
from components.chat.share_data import shared_data

# URL API
LOGIN_URL = "http://localhost:2401/auth/login"


def login_user(username, password):
    payload = {
        "username_or_email": username,
        "password": password,
    }
    try:
        # In ra thông tin đăng nhập để debug
        print("Thông tin đăng nhập:", payload)

        # Sửa thành gửi dạng JSON
        headers = {"Content-Type": "application/json"}
        response = requests.post(LOGIN_URL, json=payload, headers=headers)

        # In ra phản hồi từ server để debug
        print("Phản hồi từ server:", response.json())

        if response.status_code == 200:
            # Lưu giá trị username_email vào shared_data
            shared_data.username_or_email = username
            print("DEBUGGGGGGGGGGGGGGGGGG: " + shared_data.username_or_email)
            return True, "Đăng nhập thành công!"
        else:
            error_detail = response.json().get("detail", "Lỗi không xác định")
            return False, f"Lỗi: {error_detail}"
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"


# Giao diện đăng nhập
def create_login_page(page):
    username = ft.TextField(label="Tên đăng nhập", width=300)
    password = ft.TextField(label="Mật khẩu", password=True, width=300)
    result_message = ft.Text(color=ft.colors.RED)
    loading_overlay = ft.Container(
        visible=False,  # Ban đầu ẩn đi
        bgcolor=ft.colors.with_opacity(0.5, ft.colors.BLACK),  # Nền mờ
        content=ft.Column(
            [
                ft.ProgressRing(width=50, height=50, color=ft.colors.WHITE),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,
        expand=True,  # Chiếm toàn bộ không gian
    )

    def on_login_click(e):
        if not username.value or not password.value:
            result_message.value = "Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu!"
            result_message.color = ft.colors.RED
            page.update()
            return

        # Hiển thị loading overlay
        loading_overlay.visible = True
        result_message.value = ""  # Xóa thông báo cũ
        page.update()

        # Gọi hàm đăng nhập
        success, message = login_user(username.value, password.value)

        # Ẩn loading overlay
        loading_overlay.visible = False

        if success:
            # Chuyển hướng ngay lập tức nếu đăng nhập thành công
            page.go("/chat")
        else:
            # Hiển thị thông báo lỗi nếu đăng nhập thất bại
            result_message.value = message
            result_message.color = ft.colors.RED
            page.update()

    # Bọc Column trong một Container để căn giữa
    login_content = ft.Container(
        content=ft.Column(
            [
                ft.Text("Đăng nhập", size=24, weight="bold"),
                username,
                password,
                ft.ElevatedButton("Đăng nhập", on_click=on_login_click),
                result_message,
                ft.TextButton(
                    "Chưa có tài khoản? Đăng ký",
                    on_click=lambda e: page.go("/register"),
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,  # Căn giữa container
        expand=True,  # Mở rộng container để chiếm toàn bộ không gian
    )

    # Sử dụng Stack để chồng lớp loading lên trên giao diện đăng nhập
    return ft.Stack(
        [
            login_content,  # Giao diện đăng nhập
            loading_overlay,  # Lớp loading
        ],
        expand=True,  # Chiếm toàn bộ không gian
    )
