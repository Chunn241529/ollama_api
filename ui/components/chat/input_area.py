import webbrowser
import flet as ft
from sub_func.search import search_duckduckgo_unlimited, extract_search_info
from components.chat.utils import split_text, contains_search_keywords

selected_image = None
is_toggled_search = False
is_toggled_deepthink = False


def create_input_area(file_picker, chat, page, client, model, messages, selected_image):
    # Hàm xử lý khi người dùng chọn ảnh

    def is_toggled_search(e):
        global is_toggled_search
        is_toggled_search = not is_toggled_search
        if is_toggled_search:
            # Khi bật: nền xanh dương nhạt, chữ xanh dương đậm, icon CHECK
            toggle_search_control.bgcolor = ft.colors.BLUE_100
            toggle_search_control.color = ft.colors.BLUE_900
            toggle_search_control.text = "Search"

        else:
            # Khi tắt: nền trắng, chữ đen, icon CLOSE
            toggle_search_control.bgcolor = ft.colors.WHITE
            toggle_search_control.color = ft.colors.BLACK
            toggle_search_control.text = "Search"
        page.update()

    # Tạo ElevatedButton với màu mặc định (tắt)
    toggle_search_control = ft.ElevatedButton(
        text="Search",
        bgcolor=ft.colors.WHITE,  # Màu nền mặc định
        color=ft.colors.BLACK,  # Màu chữ mặc định
        on_click=is_toggled_search,
    )

    def is_toggled_deepthink(e):
        global is_toggled_deepthink
        is_toggled_deepthink = not is_toggled_deepthink
        if is_toggled_deepthink:
            # Khi bật: nền xanh dương nhạt, chữ xanh dương đậm, icon CHECK
            toggle_deepthink_control.bgcolor = ft.colors.BLUE_100
            toggle_deepthink_control.color = ft.colors.BLUE_900
            toggle_deepthink_control.text = "Deep Think"

        else:
            # Khi tắt: nền trắng, chữ đen, icon CLOSE
            toggle_deepthink_control.bgcolor = ft.colors.WHITE
            toggle_deepthink_control.color = ft.colors.BLACK
            toggle_deepthink_control.text = "Deep Think"
        page.update()

        # Tạo ElevatedButton với màu mặc định (tắt)

    toggle_deepthink_control = ft.ElevatedButton(
        text="Deep Think",
        bgcolor=ft.colors.WHITE,  # Màu nền mặc định
        color=ft.colors.BLACK,  # Màu chữ mặc định
        on_click=is_toggled_deepthink,
    )

    def handle_image_selection(e: ft.FilePickerResultEvent):
        global selected_image
        if e.files is not None:
            selected_image = e.files[0].path
            print(f"Đã chọn ảnh: {selected_image}")
        else:
            selected_image = None

    file_picker.on_result = handle_image_selection

    # Hàm gửi tin nhắn

    def send_message(e=None):
        global selected_image
        user_message = message_input.value.strip()
        max_line_length = 100
        lines = split_text(user_message, max_line_length)

        if user_message or selected_image:
            # Hiển thị tin nhắn của người dùng
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
                            width=None,
                            margin=ft.margin.only(bottom=30),
                        )
                    ],
                    alignment="end",
                )
            )
            message_input.value = ""
            page.update()

            # Hiển thị loading khi bot đang xử lý
            send_button.icon = None
            send_button.content = ft.ProgressRing(
                color=ft.colors.BLACK, width=20, height=20
            )
            send_button.disabled = True
            page.update()

            try:
                # Tạo container cho tin nhắn của bot
                bot_message_container = ft.Container(
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
                                        model,
                                        color=ft.colors.BLACK,
                                        size=20,
                                        weight="bold",
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

                # Thêm container vào chat
                chat.controls.append(bot_message_container)
                page.update()

                # Hiển thị 3 dòng màu xám nhạt với hiệu ứng chớp chớp
                loading_lines = ft.Container(
                    content=ft.Column(
                        [
                            ft.Container(
                                bgcolor=ft.colors.GREY_200,
                                height=10,
                                width=300,
                                border_radius=20,
                            ),
                            ft.Container(
                                bgcolor=ft.colors.GREY_200,
                                height=10,
                                width=250,
                                border_radius=20,
                            ),
                            ft.Container(
                                bgcolor=ft.colors.GREY_200,
                                height=10,
                                width=200,
                                border_radius=20,
                            ),
                        ],
                        spacing=5,
                    ),
                )

                chat.controls.append(loading_lines)
                page.update()

                loading_lines.content.controls[0].bgcolor = ft.colors.GREY_300
                loading_lines.content.controls[1].bgcolor = ft.colors.GREY_300
                loading_lines.content.controls[2].bgcolor = ft.colors.GREY_300

                # Xác định nội dung AI tùy chỉnh
                if is_toggled_search:
                    if contains_search_keywords(user_message):
                        search_results = search_duckduckgo_unlimited(user_message)
                        extracted_info = extract_search_info(search_results)
                        custom_ai = f"""
                            *Dựa trên kết quả Search \n{extracted_info}\n Hãy đưa thêm thông tin cho người dùng hiểu rõ hơn và luôn kèm theo URL các trang web.*                  
                            *Bạn là tên Như Yên. Bạn là nữ. Bạn 18 tuổi.*
                            *Trừ tiếng Anh và Tiếng Việt, bạn không đưa ngôn ngữ khác vào.*
                            *Dựa vào nội dung sau: "{user_message}", hãy cố gắng trả lời đúng ngữ cảnh, môi trường, và cách xưng hô phù hợp.*
                            *No Yapping, Limit Prose, No Fluff.*
                        """
                    else:
                        custom_ai = f"""
                            *Bạn là tên 'Như Yên'. Bạn là 'nữ'. Bạn 18 tuổi.*
                            *Trừ 'tiếng Anh' và 'Tiếng Việt', bạn không đưa ngôn ngữ khác vào.*
                            *Dựa vào nội dung sau: '{user_message}', hãy cố gắng trả lời đúng ngữ cảnh, môi trường, và cách 'xưng hô phù hợp'.*
                            *No Yapping, Limit Prose, No Fluff.*
                        """
                else:
                    custom_ai = f"""
                        *Bạn là tên 'Như Yên'. Bạn là 'nữ'. Bạn 18 tuổi.*
                        *Trừ 'tiếng Anh' và 'Tiếng Việt', bạn không đưa ngôn ngữ khác vào.*
                        *Dựa vào nội dung sau: '{user_message}', hãy cố gắng trả lời đúng ngữ cảnh, môi trường, và cách 'xưng hô phù hợp'.*
                        *No Yapping, Limit Prose, No Fluff.*
                    """

                # Tạo tin nhắn để gửi đến AI
                messages = [
                    {
                        "role": "system",
                        "content": custom_ai,
                        "images": selected_image if selected_image else None,
                    },
                    {
                        "role": "user",
                        "content": f"{user_message}\n",
                        "images": selected_image if selected_image else None,
                    },
                ]

                # Gửi yêu cầu đến AI và nhận phản hồi
                response = client.chat.completions.create(
                    model=model,
                    stream=True,
                    messages=messages,
                    temperature=0.6,
                    max_tokens=1000,
                    top_p=0.9,
                )
                # Xóa 3 dòng loading sau khi hiệu ứng kết thúc
                chat.controls.remove(loading_lines)
                page.update()

                # Hiển thị phản hồi từ bot
                full_response = ""
                bot_message_container.content.controls[1].content.value = (
                    ""  # Khởi tạo giá trị ban đầu
                )
                for chunk in response:
                    part = getattr(chunk.choices[0].delta, "content", "")
                    if part:
                        bot_message_container.content.controls[1].content.value += part
                        page.update()
                        chat.scroll_to(offset=999999, duration=200)
                        page.update()
                        full_response += part

                # Lưu phản hồi vào lịch sử tin nhắn
                messages.append(
                    {"role": "bot", "content": full_response, "images": None}
                )

            except Exception as ex:
                # Xử lý lỗi nếu có
                chat.controls.append(
                    ft.Row(
                        [
                            ft.Container(
                                content=ft.Column(
                                    [
                                        ft.Text(
                                            f"Lỗi: {str(ex)}",
                                            color=ft.colors.RED,
                                            selectable=True,
                                        )
                                    ],
                                    spacing=5,
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
            finally:
                # Khôi phục nút gửi sau khi xử lý xong
                send_button.icon = ft.icons.ARROW_UPWARD
                send_button.content = None
                send_button.disabled = False
                page.update()
                chat.scroll_to(offset=999999, duration=200)
                page.update()
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

    def update_input_width(is_focused):
        if is_focused:
            input_container.width = 600  # Khi focus, width là 600px
        else:
            input_container.width = 350  # Khi mất focus, width là 250px
        page.update()

    # Tạo TextField để nhập tin nhắn
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
        on_focus=lambda e: update_input_width(True),  # Khi focus
        on_blur=lambda e: update_input_width(False),  # Khi mất focus
    )

    # Tạo nút thêm ảnh
    add_image_button = ft.IconButton(
        icon=ft.icons.IMAGE,
        icon_color=ft.colors.BLACK,
        bgcolor=ft.colors.WHITE,
        on_click=lambda e: file_picker.pick_files(
            allowed_extensions=["jpg", "jpeg", "png"],
            dialog_title="Chọn ảnh",
        ),
    )

    # Tạo nút Send với hiệu ứng loading
    send_button = ft.IconButton(
        icon=ft.icons.SEND,
        icon_color=ft.colors.BLACK,
        bgcolor=ft.colors.WHITE,
        on_click=send_message,
    )
    input_container = ft.Container(
        content=ft.Column(
            [
                message_input,
                ft.Row(
                    [
                        toggle_deepthink_control,
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
        width=350,
        animate=ft.animation.Animation(300, "easeInOut"),
    )
    return input_container
