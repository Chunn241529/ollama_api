import flet as ft
from openai import OpenAI
from sub_func.search import search_duckduckgo_unlimited, extract_search_info

# Cấu hình API key của OpenAI (thay thế bằng API key thực)
client = OpenAI(base_url=f"http://localhost:11434/v1", api_key="ollama")
messages = []
# Biến lưu hình ảnh được chọn
selected_image = None
model = "llama3.1:8b"


def main(page: ft.Page):

    page.theme_mode = ft.ThemeMode.LIGHT
    page.title = "ChunGPT"
    page.horizontal_alignment = "center"
    page.padding = 10
    page.window_width = 700  # Đặt chiều rộng cửa sổ ứng dụng
    page.window_height = 700  # Đặt chiều cao cửa sổ ứng dụng

    # Tạo FilePicker
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)  # Thêm FilePicker vào overlay của page

    # Hàm xử lý khi người dùng chọn ảnh
    def handle_image_selection(e: ft.FilePickerResultEvent):
        global selected_image
        if e.files is not None:
            selected_image = e.files[0].path  # Lưu đường dẫn ảnh
            print(f"Đã chọn ảnh: {selected_image}")
        else:
            selected_image = None

    # Đăng ký sự kiện khi người dùng chọn ảnh
    file_picker.on_result = handle_image_selection

    # Tạo header
    header = ft.Row(
        controls=[
            # Icon tạo mới tin nhắn bên trái
            ft.IconButton(icon=ft.icons.MENU, icon_size=20),
            # Spacer để đẩy các nút bên phải sang phải
            ft.Container(expand=True),
            ft.IconButton(icon=ft.icons.CREATE, icon_size=20),
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Tạo ListView để hiển thị tin nhắn
    chat = ft.ListView(expand=True, spacing=5, auto_scroll=True)

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

    import webbrowser

    def handle_link_click(e):
        """
        Hàm xử lý khi người dùng nhấp vào liên kết trong Markdown.
        """
        # Lấy URL từ sự kiện
        url = e.data
        print(f"Đang mở liên kết: {url}")

        # Mở liên kết trong trình duyệt mặc định
        webbrowser.open(url)

    # Hàm gửi tin nhắn
    def send_message(e=None):
        global selected_image  # Sử dụng biến toàn cục
        user_message = message_input.value.strip()

        # Sử dụng hàm split_text để chia nhỏ tin nhắn
        max_line_length = 100  # Độ dài tối đa của mỗi dòng
        lines = split_text(user_message, max_line_length)

        if user_message or selected_image:
            # Hiển thị tin nhắn của người dùng (bên phải)
            chat.controls.append(
                ft.Row(
                    [
                        # Thêm từng dòng vào Column
                        ft.Container(
                            content=ft.Column(
                                [
                                    ft.Text(
                                        line,
                                        color=ft.colors.BLACK,
                                        size=14,
                                    )
                                    for line in lines
                                ]
                                + (
                                    [
                                        ft.Image(
                                            src=selected_image, width=200, height=200
                                        )
                                    ]
                                    if selected_image
                                    else []
                                ),
                                spacing=5,
                            ),
                            bgcolor=ft.colors.GREY_200,
                            padding=10,
                            border_radius=25,
                            width=None,  # Cho phép container co giãn theo nội dung
                            margin=ft.margin.only(
                                bottom=30
                            ),  # Tạo khoảng cách bên phải
                        )
                    ],
                    alignment="end",
                )
            )
            message_input.value = ""  # Xóa nội dung trong ô nhập
            page.update()

            # Hiển thị loading trên nút Send
            send_button.icon = None
            send_button.content = ft.ProgressRing(
                color=ft.colors.BLACK, width=20, height=20
            )
            send_button.disabled = True
            page.update()

            try:
                # Tạo một container để hiển thị tin nhắn của bot
                bot_message_container = ft.Container(
                    content=ft.Column(
                        [
                            # Hàng chứa avatar và tên model
                            ft.Row(
                                [
                                    # Avatar của bot (sử dụng ft.Image)
                                    ft.Image(
                                        src="ui\\storage\\assets\\img\\1.jpg",  # Đường dẫn tệp cục bộ
                                        width=40,  # Điều chỉnh kích thước
                                        height=40,
                                        fit=ft.ImageFit.COVER,  # Đảm bảo hình ảnh phù hợp với kích thước
                                        border_radius=20,  # Làm tròn góc để giống avatar
                                    ),
                                    # Tên model
                                    ft.Text(
                                        model,  # Tên model
                                        color=ft.colors.BLACK,
                                        size=20,
                                        weight="bold",
                                    ),
                                ],
                                spacing=20,  # Khoảng cách giữa avatar và tên model
                                alignment="start",  # Căn chỉnh bên trái
                            ),
                            # Nội dung tin nhắn của bot
                            ft.Container(
                                content=ft.Markdown(
                                    "",  # Ban đầu chưa có nội dung
                                    extension_set="gitHubWeb",  # Sử dụng bộ Markdown cơ bản
                                    selectable=True,  # Cho phép người dùng chọn văn bản
                                    fit_content=True,  # Điều chỉnh chiều rộng tự động (không cần width)
                                    on_tap_link=handle_link_click,  # Xử lý khi nhấp vào liên kết
                                    code_style=ft.TextStyle(
                                        color=ft.colors.WHITE,  # Màu chữ của code
                                        font_family="monospace",  # Font chữ cho code
                                        size=14,
                                        weight="bold",
                                    ),
                                    code_theme="monokai",  # Chủ đề màu cho code (dark hoặc light)
                                ),
                                padding=10,  # Padding bên trong container
                                border_radius=10,  # Bo góc container
                            ),
                        ],
                        spacing=10,
                    ),
                    padding=10,
                )

                # Thêm container vào chat
                chat.controls.append(bot_message_container)
                page.update()

                if contains_search_keywords(user_message):
                    # Nếu có, thực hiện tìm kiếm
                    search_results = search_duckduckgo_unlimited(user_message)
                    extracted_info = extract_search_info(search_results)

                    # Tạo custom_ai với thông tin trích xuất và URL
                    custom_ai = f"""
                        *Dựa trên kết quả tìm kiếm \n{extracted_info}\n Hãy đưa thêm thông tin cho người dùng hiểu rõ hơn và luôn kèm theo URL các trang web*                  
                        *Bạn là tên Như Yên. Bạn là nữ. Bạn 18 tuổi.*
                        *Trừ tiếng Anh và Tiếng Việt, bạn không đưa ngôn ngữ khác vào.*
                        *Hãy cố gắng xưng hô cho đúng.*
                        *No Yapping, Limit Prose, No Fluff.*
                    """
                else:
                    # Nếu không, trò chuyện bình thường
                    custom_ai = """
                        *Bạn là tên Như Yên. Bạn là nữ. Bạn 18 tuổi.*
                        *Trừ tiếng Anh và Tiếng Việt, bạn không đưa ngôn ngữ khác vào.*
                        *Hãy cố gắng xưng hô cho đúng.*
                        *No Yapping, Limit Prose, No Fluff.*
                    """

                messages = [
                    {
                        "role": "system",
                        "content": custom_ai,
                        "images": (
                            selected_image if selected_image else None
                        ),  # Thêm ảnh nếu có
                    },
                    {
                        "role": "user",
                        "content": f"{user_message}\n",
                        "images": (
                            selected_image if selected_image else None
                        ),  # Thêm ảnh nếu có
                    },
                ]

                # Gọi API ChatGPT với stream=True
                response = client.chat.completions.create(
                    model=model,
                    stream=True,  # Sử dụng stream để nhận từng phần phản hồi
                    messages=messages,
                    temperature=0.6,  # Độ sáng tạo của mô hình (từ 0 đến 1)
                    max_tokens=1000,  # Số lượng tối đa token cho phản hồi
                    top_p=0.9,  # Sử dụng nucleus sampling (0.0 đến 1.0)
                )
                full_response = ""
                # Xử lý từng phần phản hồi
                for chunk in response:
                    part = getattr(chunk.choices[0].delta, "content", "")
                    if part:
                        # Cập nhật nội dung tin nhắn của bot
                        bot_message_container.content.controls[1].content.value += part
                        page.update()

                        # Tự động cuộn xuống dưới cùng
                        chat.scroll_to(
                            offset=999999, duration=200
                        )  # Cuộn xuống dưới cùng
                        page.update()
                        full_response += part
                messages.append(
                    {
                        "role": "bot",
                        "content": full_response,
                        "images": None,
                    }
                )

            except Exception as ex:
                # Hiển thị thông báo lỗi nếu có
                chat.controls.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(f"Lỗi: {str(ex)}", color=ft.colors.RED),
                                    ],
                                    spacing=5,
                                ),
                                bgcolor=ft.colors.GREY_800,
                                padding=10,
                                border_radius=10,
                                width=700,  # Giới hạn chiều rộng tối đa
                            ),
                        ],
                        alignment="start",
                    )
                )
                # Tự động cuộn xuống dưới cùng khi có lỗi
                chat.scroll_to(offset=999999, duration=200)
                page.update()
            finally:
                # Khôi phục nút Send về trạng thái ban đầu
                send_button.icon = ft.icons.ARROW_UPWARD
                send_button.content = None
                send_button.disabled = False
                page.update()

                # Tự động cuộn xuống dưới cùng sau khi hoàn thành
                chat.scroll_to(offset=999999, duration=200)
                page.update()

                # Reset selected_image sau khi gửi
                selected_image = None
                page.update()

    # Hàm xử lý sự kiện bàn phím
    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Enter" and not e.shift:
            # Nếu nhấn Enter mà không nhấn Shift, gửi tin nhắn
            send_message()
            page.update()

    # Đăng ký sự kiện bàn phím toàn cục
    page.on_keyboard_event = on_keyboard

    # Tạo TextField để nhập tin nhắn
    message_input = ft.TextField(
        hint_text="Nhập tin nhắn...",
        hint_style=ft.TextStyle(color=ft.colors.GREY_200),
        expand=True,
        autofocus=True,
        border_color=ft.colors.GREY_800,
        bgcolor=ft.colors.GREY_800,
        color=ft.colors.WHITE,
        multiline=True,  # Cho phép nhập nhiều dòng
        min_lines=1,  # Số dòng tối thiểu
        max_lines=10,  # Số dòng tối đa
        on_focus=lambda e: update_input_width(True),  # Khi focus
        on_blur=lambda e: update_input_width(False),  # Khi mất focus
    )

    # Tạo nút thêm ảnh
    add_image_button = ft.IconButton(
        icon=ft.icons.IMAGE,
        icon_color=ft.colors.BLACK,
        bgcolor=ft.colors.WHITE,
        on_click=lambda e: file_picker.pick_files(
            allowed_extensions=["jpg", "jpeg", "png"],  # Chỉ cho phép chọn file ảnh
            dialog_title="Chọn ảnh",  # Tiêu đề hộp thoại
        ),
    )

    # Tạo nút Send với hiệu ứng loading
    send_button = ft.IconButton(
        icon=ft.icons.SEND,
        icon_color=ft.colors.BLACK,
        bgcolor=ft.colors.WHITE,
        on_click=send_message,  # Gọi hàm send_message khi nhấn nút
    )

    # Tạo Container chứa input và các nút
    input_container = ft.Container(
        content=ft.Column(
            [
                message_input,  # Ô nhập tin nhắn (ở trên)
                ft.Row(
                    [
                        ft.Container(expand=True),
                        add_image_button,  # Nút thêm ảnh (bên trái)
                        send_button,  # Nút gửi (bên phải)
                    ],
                    spacing=10,  # Khoảng cách giữa các nút
                ),
            ],
            spacing=10,  # Khoảng cách giữa ô nhập và các nút
        ),
        padding=10,
        bgcolor=ft.colors.GREY_800,
        border_radius=25,
        width=350,  # Mặc định width là 250px
        animate=ft.animation.Animation(300, "easeInOut"),  # Hiệu ứng animate
    )

    # Hàm cập nhật width của input_container
    def update_input_width(is_focused):
        if is_focused:
            input_container.width = 600  # Khi focus, width là 600px
        else:
            input_container.width = 350  # Khi mất focus, width là 250px
        page.update()

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

    # Tạo giao diện
    page.add(
        ft.Column(
            [
                header,  # Hiển thị header
                chat,  # Hiển thị tin nhắn
                ft.Row(
                    [
                        input_container,  # Container chứa input và nút
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,  # Căn giữa theo chiều ngang
                ),
            ],
            expand=True,
            width=700,  # Đặt chiều rộng cố định
        )
    )


# Chạy ứng dụng
ft.app(target=main)
