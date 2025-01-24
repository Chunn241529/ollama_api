# register.py
import flet as ft
import requests

# URL API
REGISTER_URL = "http://localhost:2401/auth/register"


# Hàm xử lý đăng ký
def register_user(username, password, email, phone, full_name, avatar):
    payload = {
        "username": username,
        "password": password,
        "verify_code": "1234",
        "email": email,
        "phone": phone,
        "full_name": full_name,
        "avatar": avatar,
    }
    try:
        response = requests.post(REGISTER_URL, json=payload)
        if response.status_code == 200:
            return True, "Đăng ký thành công!"
        else:
            error_detail = response.json().get("detail", "Lỗi không xác định")
            return False, f"Lỗi: {error_detail}"
    except Exception as e:
        return False, f"Lỗi kết nối: {str(e)}"


# Giao diện đăng ký
def create_register_page(page):
    username = ft.TextField(label="Tên đăng nhập", width=300)
    password = ft.TextField(label="Mật khẩu", password=True, width=300)
    email = ft.TextField(label="Email", width=300)
    phone = ft.TextField(label="Số điện thoại", width=300)
    full_name = ft.TextField(label="Họ và tên", width=300)
    avatar = ft.TextField(label="Avatar URL", width=300)
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

    def on_register_click(e):
        if not username.value or not password.value or not email.value:
            result_message.value = "Vui lòng nhập đầy đủ thông tin!"
            result_message.color = ft.colors.RED
            page.update()
            return

        # Hiển thị loading overlay
        loading_overlay.visible = True
        result_message.value = ""  # Xóa thông báo cũ
        page.update()

        success, message = register_user(
            username.value,
            password.value,
            email.value,
            phone.value,
            full_name.value,
            avatar.value,
        )
        result_message.value = message
        result_message.color = ft.colors.GREEN if success else ft.colors.RED
        page.update()

        # Ẩn loading overlay
        loading_overlay.visible = False

        # Chuyển hướng đến trang login sau khi đăng ký thành công
        if success:
            page.go("/login")

    return ft.Container(
        content=ft.Column(
            [
                ft.Text("Đăng ký", size=24, weight="bold"),
                username,
                password,
                email,
                phone,
                full_name,
                avatar,
                ft.ElevatedButton("Đăng ký", on_click=on_register_click),
                result_message,
                ft.TextButton(
                    "Đã có tài khoản? Đăng nhập", on_click=lambda e: page.go("/login")
                ),
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        ),
        alignment=ft.alignment.center,  # Căn giữa container
        expand=True,  # Mở rộng container để chiếm toàn bộ không gian
    )
