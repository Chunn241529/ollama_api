import flet as ft
import subprocess


# Fetch available models dynamically
def get_available_models():
    try:
        result = subprocess.run(
            ["ollama", "ls"], capture_output=True, text=True, check=True
        )
        lines = result.stdout.strip().split("\n")
        if lines:
            # Skip the header row and extract only the `NAME` column
            models = [line.split()[0] for line in lines[1:]]
            return models
        return []
    except subprocess.CalledProcessError as e:
        print("Không thể lấy danh sách model:", e)
        return []


def create_header(update_model):
    # Tạo một tham chiếu đến widget Text
    text_ref = ft.Ref[ft.Text]()
    # Tạo một tham chiếu đến Drawer (menu trượt)
    drawer_ref = ft.Ref[ft.Container]()

    def on_dropdown_select(e):
        # Cập nhật nội dung của Text khi chọn một tùy chọn
        selected_model = e.control.text
        text_ref.current.value = selected_model
        text_ref.current.update()
        # Cập nhật model trong main.py
        update_model(selected_model)

    def toggle_drawer(e):
        # Đảo ngược trạng thái hiển thị của drawer menu
        if drawer_ref.current.left == -250:  # Nếu drawer đang ẩn
            drawer_ref.current.left = 0  # Hiển thị drawer
        else:
            drawer_ref.current.left = -250  # Ẩn drawer
        drawer_ref.current.update()

    def close_drawer(e):
        # Đóng drawer menu
        drawer_ref.current.left = -250  # Ẩn drawer
        drawer_ref.current.update()

    # Lấy danh sách models
    models = get_available_models()

    # Tạo các tùy chọn cho dropdown từ danh sách models
    dropdown_items = [
        ft.PopupMenuItem(text=model, on_click=on_dropdown_select) for model in models
    ]

    return ft.Stack(
        controls=[
            # Phần header
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.MENU,
                        icon_size=20,
                        icon_color=ft.colors.WHITE,  # Icon màu trắng
                        on_click=toggle_drawer,  # Thêm sự kiện click để mở drawer
                    ),  # Nút menu bên trái
                    ft.Container(expand=True),  # Khoảng trống giữa menu và text
                    ft.Row(
                        controls=[
                            ft.Text(
                                "ChunGPT",
                                size=16,
                                weight=ft.FontWeight.BOLD,
                                ref=text_ref,
                            ),  # Text "Trung tâm"
                            ft.PopupMenuButton(  # Nút dropdown
                                icon=ft.icons.ARROW_DROP_DOWN,
                                icon_color=ft.colors.WHITE,  # Icon màu trắng
                                items=dropdown_items,  # Sử dụng danh sách models làm tùy chọn
                            ),
                        ],
                        spacing=5,  # Khoảng cách giữa text và dropdown
                    ),
                    ft.Container(
                        expand=True
                    ),  # Khoảng trống giữa dropdown và nút bên phải
                    ft.IconButton(
                        icon=ft.icons.CREATE,
                        icon_size=20,
                        icon_color=ft.colors.WHITE,  # Icon màu trắng
                    ),  # Nút bên phải
                ],
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            ),
            # Drawer menu (menu trượt)
            ft.Container(
                ref=drawer_ref,
                content=ft.Column(
                    controls=[
                        # Nút đóng drawer menu
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.icons.CLOSE,
                                    icon_size=20,
                                    icon_color=ft.colors.WHITE,
                                    on_click=close_drawer,  # Sự kiện đóng drawer
                                ),
                            ],
                            alignment=ft.MainAxisAlignment.END,
                        ),
                        # Các mục trong drawer menu
                        ft.Container(
                            padding=ft.padding.all(20),
                            content=ft.Column(
                                controls=[
                                    ft.Text("Menu", size=18, weight=ft.FontWeight.BOLD),
                                    ft.Divider(),  # Đường kẻ ngăn cách
                                    ft.ListTile(
                                        title=ft.Text("Mục 1"),
                                        leading=ft.Icon(ft.icons.HOME),
                                        on_click=lambda e: print("Mục 1 được chọn"),
                                    ),
                                    ft.ListTile(
                                        title=ft.Text("Mục 2"),
                                        leading=ft.Icon(ft.icons.SETTINGS),
                                        on_click=lambda e: print("Mục 2 được chọn"),
                                    ),
                                    ft.ListTile(
                                        title=ft.Text("Mục 3"),
                                        leading=ft.Icon(ft.icons.INFO),
                                        on_click=lambda e: print("Mục 3 được chọn"),
                                    ),
                                ],
                                spacing=10,
                            ),
                        ),
                    ],
                ),
                bgcolor=ft.colors.BACKGROUND,  # Màu nền của drawer menu
                width=250,  # Chiều rộng của drawer menu
                top=0,
                left=-250,  # Ban đầu drawer menu ẩn bên trái màn hình
                bottom=0,
                animate_position=ft.animation.Animation(
                    300, ft.AnimationCurve.EASE_IN_OUT
                ),
            ),
        ],
    )
