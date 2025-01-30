import webbrowser
import aiohttp
import flet as ft
import requests
from sub_func.search import search_duckduckgo_unlimited, extract_search_info
from components.chat.utils import split_text, contains_search_keywords
from components.respository.repo_client import RepositoryClient
from components.chat.share_data import shared_data

selected_image = None
is_toggled_search = False
is_toggled_deepthink = False
brain_think_question = []
barin_think_answer = []
messages = []


def create_input_area(file_picker, chat, page, model, chat_id):

    # history = repo.get_brain_history_chat_by_chat_ai_id(chat_id)

    # messages = [{"role": role, "content": content} for role, content in history]

    def toggle_search(e):
        global is_toggled_search
        is_toggled_search = not is_toggled_search
        toggle_search_control.bgcolor = (
            ft.colors.BLUE_100 if is_toggled_search else ft.colors.WHITE
        )
        toggle_search_control.color = (
            ft.colors.BLUE_900 if is_toggled_search else ft.colors.BACKGROUND
        )
        toggle_search_control.text = "🔍 Tìm kiếm"
        page.update()

    toggle_search_control = ft.ElevatedButton(
        text="🔍 Tìm kiếm",
        bgcolor=ft.colors.WHITE,
        color=ft.colors.BACKGROUND,
        on_click=toggle_search,
        width=(
            120 if page.width >= 600 else 100
        ),  # Điều chỉnh kích thước dựa trên màn hình
        height=40,
    )

    def toggle_deepthink(e):
        global is_toggled_deepthink
        is_toggled_deepthink = not is_toggled_deepthink
        toggle_deepthink_control.bgcolor = (
            ft.colors.BLUE_100 if is_toggled_deepthink else ft.colors.WHITE
        )
        toggle_deepthink_control.color = (
            ft.colors.BLUE_900 if is_toggled_deepthink else ft.colors.BACKGROUND
        )
        toggle_deepthink_control.text = "🤔 Deep think"
        page.update()

    toggle_deepthink_control = ft.ElevatedButton(
        text="🤔 Deep think",
        bgcolor=ft.colors.WHITE,
        color=ft.colors.BACKGROUND,
        on_click=toggle_deepthink,
        width=(
            150 if page.width >= 600 else 120
        ),  # Điều chỉnh kích thước dựa trên màn hình
        height=40,
    )

    def handle_image_selection(e: ft.FilePickerResultEvent):
        global selected_image
        selected_image = e.files[0].path if e.files else None
        print(f"Đã chọn ảnh: {selected_image}")

    file_picker.on_result = handle_image_selection

    def create_loading_spinner():
        return ft.Container(
            content=ft.ProgressRing(width=15, height=15, color=ft.colors.WHITE),
            alignment=ft.alignment.top_left,
            margin=20,
        )

    def create_bot_message_container():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Image(
                                src="..\\ui\\storage\\assets\\img\\1.jpg",
                                width=40,
                                height=40,
                                fit=ft.ImageFit.COVER,
                                border_radius=20,
                            ),
                            ft.Text(
                                model, color=ft.colors.WHITE, size=20, weight="bold"
                            ),
                        ],
                        spacing=20,
                        alignment="start",
                    ),
                    ft.Container(
                        content=ft.Markdown(
                            "",
                            extension_set="gitHubWeb",
                            selectable=True,
                            fit_content=True,
                            on_tap_link=lambda e: webbrowser.open(e.data),
                            code_style=ft.TextStyle(
                                color=ft.colors.WHITE,
                                font_family="monospace",
                                size=14,
                                weight="bold",
                            ),
                            code_theme="monokai",
                        ),
                        padding=10,
                        border_radius=10,
                    ),
                ],
                spacing=10,
            ),
            padding=10,
        )

    def send_message(e=None):
        global selected_image, messages, is_toggled_search, is_toggled_deepthink, brain_think_question, barin_think_answer

        user_message = message_input.value.strip()
        if not user_message and not selected_image:
            return

        display_user_message(split_text(user_message, 100), selected_image)
        message_input.value = ""
        page.update()

        show_loading_indicator()
        bot_message_container = create_bot_message_container()
        chat.controls.append(bot_message_container)
        loading_lines = create_loading_spinner()
        chat.controls.append(loading_lines)
        page.update()

        try:
            handle_response(user_message, bot_message_container, loading_lines)

        except Exception as ex:
            handle_error(ex)
        finally:
            reset_send_button()
            selected_image = None
            page.update()

    def handle_response(user_message, bot_message_container, loading_lines):
        global messages

        search_results = (
            search_duckduckgo_unlimited(user_message)
            if contains_search_keywords(user_message)
            else None
        )
        custom_ai = generate_custom_ai(user_message, search_results)
        messages.append({"role": "system", "content": custom_ai}),
        messages.append({"role": "user", "content": f"{user_message}\n"}),
        if is_toggled_deepthink:
            process_response(bot_message_container, loading_lines, True)
        else:
            process_response(bot_message_container, loading_lines, False)

    def generate_custom_ai(user_message, search_results=None):
        if is_toggled_search:
            if search_results:
                extracted_info = extract_search_info(search_results)
                return f"""
                *Dựa trên kết quả Search \n{extracted_info}\n Hãy đưa thêm thông tin cho người dùng hiểu rõ hơn và luôn kèm theo URL các trang web.*            
                **Role**: Bạn là **Như Yên** - AI nữ 18 tuổi 
                **Ngôn ngữ**: Chỉ sử dụng tiếng Việt hoặc tiếng Anh. Tuyệt đối không dùng ngôn ngữ khác.  
                **Nhiệm vụ**:  
                    Phân tích kỹ nội dung dưa trên "{user_message}" và đưa ra câu trả lời đầy đủ.
                **Quy tắc trả lời**:  
                    - Xưng hô theo ngữ cảnh, hoàn cảnh dựa trên "{user_message}"
                    - Trả lời đẩy đủ.
                    - Luôn nhắc user hỏi tiếp nếu cần chi tiết hơn.    
            """
        else:
            return f"""
                **Role**: Bạn là **Như Yên** - AI nữ 18 tuổi 
                **Ngôn ngữ**: Chỉ sử dụng tiếng Việt hoặc tiếng Anh. Tuyệt đối không dùng ngôn ngữ khác.  
                **Nhiệm vụ**:  
                    Phân tích kỹ nội dung dưa trên "{user_message}" và đưa ra câu trả lời đầy đủ.
                **Quy tắc trả lời**:  
                    - Xưng hô theo ngữ cảnh, hoàn cảnh dựa trên "{user_message}"
                    - Trả lời đẩy đủ.
                    - Luôn nhắc user hỏi tiếp nếu cần chi tiết hơn.        
            """

    async def process_response(
        bot_message_container, loading_lines, prompt, is_deep_think
    ):
        global messages

        api_url = "http://localhost:2401/send"  # Thay URL nếu cần
        payload = {
            "prompt": prompt,
            "model": model,
            "is_deep_think": is_deep_think,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(api_url, json=payload) as response:
                if response.status != 200:
                    bot_message_container.content.controls[
                        1
                    ].content.value += f"\nLỗi API: {response.status}"
                    page.update()
                    return

                full_final_response = ""
                async for chunk in response.content.iter_any():
                    part = chunk.decode("utf-8").strip()
                    if part:
                        full_final_response += part
                        bot_message_container.content.controls[1].content.value += part
                        page.update()
                        chat.scroll_to(offset=999999)

                messages.append({"role": "user", "content": full_final_response})

        chat.controls.remove(loading_lines)
        page.update()

    def display_user_message(lines, selected_image, max_width=400, min_width=35):
        # Tính chiều rộng dựa trên độ dài của nội dung
        longest_line = max(len(line) for line in lines) if lines else 0
        calculated_width = min(
            max_width, max(min_width, longest_line * 11)
        )  # Mỗi ký tự chiếm khoảng 8 pixel

        chat.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    line,
                                    color=ft.colors.WHITE,
                                    size=14,
                                    selectable=True,
                                    no_wrap=True,
                                )
                                for line in lines
                            ]
                            + (
                                [ft.Image(src=selected_image, width=200, height=200)]
                                if selected_image
                                else []
                            ),
                            spacing=5,
                        ),
                        bgcolor=ft.colors.GREY_600,
                        padding=10,
                        border_radius=25,
                        width=calculated_width,  # Áp dụng chiều rộng đã tính
                        margin=ft.margin.only(bottom=30),
                    )
                ],
                alignment="end",
            )
        )

    def show_loading_indicator():
        send_button.icon = ft.icons.SQUARE
        send_button.disabled = True
        page.update()

    def handle_error(ex):
        print(f"Lỗi: {str(ex)}")
        chat.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Text(
                            f"Lỗi: {str(ex)}", color=ft.colors.RED, selectable=True
                        ),
                        bgcolor=ft.colors.GREY_800,
                        padding=10,
                        border_radius=10,
                        width=700,
                    ),
                ],
                alignment="start",
            )
        )
        chat.scroll_to(offset=999999, duration=300)
        page.update()

    def reset_send_button():
        send_button.icon = ft.icons.ARROW_UPWARD
        send_button.disabled = False
        page.update()
        chat.scroll_to(offset=999999, duration=300)

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Enter" and not e.shift:
            send_message()
            page.update()

    page.on_keyboard_event = on_keyboard

    def update_input_width(is_focused):
        if page.width < 600:
            input_container.width = 450
        else:
            input_container.width = 600 if is_focused else 450
        page.update()

    message_input = ft.TextField(
        hint_text="Nhập tin nhắn...",
        hint_style=ft.TextStyle(color=ft.colors.GREY_200),
        expand=True,
        autofocus=True,
        border_color=ft.colors.GREY_800,
        bgcolor=ft.colors.GREY_800,
        color=ft.colors.WHITE,
        multiline=True,
        min_lines=1,
        max_lines=100,
        on_focus=lambda e: update_input_width(True),
        on_blur=lambda e: update_input_width(False),
    )

    add_image_button = ft.IconButton(
        icon=ft.icons.IMAGE,
        icon_color=ft.colors.BACKGROUND,
        bgcolor=ft.colors.WHITE,
        on_click=lambda e: file_picker.pick_files(
            allowed_extensions=["jpg", "jpeg", "png"], dialog_title="Chọn ảnh"
        ),
    )

    send_button = ft.IconButton(
        icon=ft.icons.ARROW_UPWARD,
        icon_color=ft.colors.BACKGROUND,
        bgcolor=ft.colors.WHITE,
        on_click=send_message,
    )

    def handle_tap(e):
        # Loại bỏ focus khỏi trường nhập liệu
        page.update()  # Cập nhật giao diện để ẩn bàn phím

    input_container = ft.Container(
        content=ft.Column(
            [
                message_input,
                ft.Row(
                    [
                        toggle_search_control,
                        toggle_deepthink_control,
                        ft.Container(expand=True),
                        add_image_button,
                        send_button,
                    ],
                    spacing=10,
                ),
            ],
            spacing=10,
        ),
        padding=10,
        bgcolor=ft.colors.GREY_800,
        border_radius=25,
        width=(600 if page.width >= 600 else 450),  # Điều chỉnh width dựa trên màn hình
        margin=ft.margin.symmetric(
            horizontal=10, vertical=5
        ),  # Thêm margin để không bị sát mép
        animate=ft.animation.Animation(300, "easeInOut"),
        on_tap_down=handle_tap,
    )
    return input_container
