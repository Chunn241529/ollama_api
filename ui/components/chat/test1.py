import webbrowser
import flet as ft
from sub_func.search import search_duckduckgo_unlimited, extract_search_info
from components.chat.utils import split_text, contains_search_keywords

selected_image = None
is_toggled_search = False
brain_think_question = []
barin_think_answer = []
messages = []


def create_input_area(file_picker, chat, page, client, model):
    def toggle_search(e):
        global is_toggled_search
        is_toggled_search = not is_toggled_search
        toggle_search_control.bgcolor = (
            ft.colors.BLUE_100 if is_toggled_search else ft.colors.WHITE
        )
        toggle_search_control.color = (
            ft.colors.BLUE_900 if is_toggled_search else ft.colors.BLACK
        )
        toggle_search_control.text = "🔍 Tìm kiếm"
        page.update()

    toggle_search_control = ft.ElevatedButton(
        text="🔍 Tìm kiếm",
        bgcolor=ft.colors.WHITE,
        color=ft.colors.BLACK,
        on_click=toggle_search,
        width=(
            120 if page.width >= 600 else 100
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
            content=ft.ProgressRing(width=15, height=15, color=ft.colors.BLACK),
            alignment=ft.alignment.bottom_left,
            margin=20,
        )

    def create_bot_message_container():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Row(
                        [
                            ft.Image(
                                src="ui\\storage\\assets\\img\\1.jpg",
                                width=40,
                                height=40,
                                fit=ft.ImageFit.COVER,
                                border_radius=20,
                            ),
                            ft.Text(
                                model, color=ft.colors.BLACK, size=20, weight="bold"
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
        global selected_image, messages, is_toggled_search, brain_think_question, barin_think_answer

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
            if is_toggled_search:
                handle_search(user_message, bot_message_container, loading_lines)
            else:
                handle_default(user_message, bot_message_container, loading_lines)
        except Exception as ex:
            handle_error(ex)
        finally:
            reset_send_button()
            selected_image = None
            page.update()

    def handle_search(user_message, bot_message_container, loading_lines):
        global messages

        search_results = (
            search_duckduckgo_unlimited(user_message)
            if contains_search_keywords(user_message)
            else None
        )
        custom_ai = generate_custom_ai(user_message, search_results)
        messages.append({"role": "system", "content": custom_ai}),
        messages.append({"role": "user", "content": f"{user_message}\n"}),
        process_response(bot_message_container, loading_lines)

    def handle_default(user_message, bot_message_container, loading_lines):
        global messages
        custom_ai = generate_custom_ai(user_message)
        messages.append({"role": "system", "content": custom_ai}),
        messages.append({"role": "user", "content": f"{user_message}\n"}),

        process_response(bot_message_container, loading_lines)

    def generate_custom_ai(user_message, search_results=None):
        if search_results:
            extracted_info = extract_search_info(search_results)
            return f"""
                *Dựa trên kết quả Search \n{extracted_info}\n Hãy đưa thêm thông tin cho người dùng hiểu rõ hơn và luôn kèm theo URL các trang web.*                  
                *Bạn là tên Như Yên. Bạn là nữ. Bạn 18 tuổi.*
                *Trừ tiếng Anh và Tiếng Việt, bạn không đưa ngôn ngữ khác vào.*
                *Dựa vào nội dung sau: "{user_message}", hãy cố gắng trả lời đúng ngữ cảnh, môi trường, và cách xưng hô phù hợp.*
                *No Yapping, Limit Prose, No Fluff.*
            """
        return f"""
            *Bạn là tên 'Như Yên'. Bạn là 'nữ'. Bạn 18 tuổi.*
            *Trừ 'tiếng Anh' và 'Tiếng Việt', bạn không đưa ngôn ngữ khác vào.*
            *Dựa vào nội dung sau: '{user_message}', hãy cố gắng trả lời đúng ngữ cảnh, môi trường, và cách 'xưng hô phù hợp'.*
            *No Yapping, Limit Prose, No Fluff.*
        """

    def process_response(bot_message_container, loading_lines):
        global messages
        response = display_bot_message_markdown(messages)
        full_final_response = ""
        for chunk in response:
            part = getattr(chunk.choices[0].delta, "content", "")
            if part:
                full_final_response += part
                bot_message_container.content.controls[1].content.value += part
                page.update()
                chat.scroll_to(offset=999999, duration=200)
        messages.append({"role": "user", "content": full_final_response})
        chat.controls.remove(loading_lines)
        page.update()

    def display_user_message(lines, selected_image):
        chat.controls.append(
            ft.Row(
                [
                    ft.Container(
                        content=ft.Column(
                            [
                                ft.Text(
                                    line,
                                    color=ft.colors.BLACK,
                                    size=14,
                                    selectable=True,
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
                        bgcolor=ft.colors.GREY_200,
                        padding=10,
                        border_radius=25,
                        width=None,
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
        chat.scroll_to(offset=999999, duration=200)
        page.update()

    def reset_send_button():
        send_button.icon = ft.icons.ARROW_UPWARD
        send_button.disabled = False
        page.update()
        chat.scroll_to(offset=999999, duration=200)

    def display_bot_message_markdown(final_prompt):
        return client.chat.completions.create(
            model=model,
            stream=True,
            messages=final_prompt,
            temperature=0.6,
            max_tokens=5500,
            top_p=0.9,
        )

    def on_keyboard(e: ft.KeyboardEvent):
        if e.key == "Enter" and not e.shift:
            send_message()
            page.update()

    page.on_keyboard_event = on_keyboard

    def update_input_width(is_focused):
        if page.width < 600:
            input_container.width = 250
        else:
            input_container.width = 600 if is_focused else 350
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
        max_lines=10,
        on_focus=lambda e: update_input_width(True),
        on_blur=lambda e: update_input_width(False),
    )

    add_image_button = ft.IconButton(
        icon=ft.icons.IMAGE,
        icon_color=ft.colors.BLACK,
        bgcolor=ft.colors.WHITE,
        on_click=lambda e: file_picker.pick_files(
            allowed_extensions=["jpg", "jpeg", "png"], dialog_title="Chọn ảnh"
        ),
    )

    send_button = ft.IconButton(
        icon=ft.icons.ARROW_UPWARD,
        icon_color=ft.colors.BLACK,
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
        width=(350 if page.width >= 600 else 150),  # Điều chỉnh width dựa trên màn hình
        margin=ft.margin.symmetric(
            horizontal=10, vertical=5
        ),  # Thêm margin để không bị sát mép
        animate=ft.animation.Animation(300, "easeInOut"),
        on_tap_down=handle_tap,
    )
    return input_container
