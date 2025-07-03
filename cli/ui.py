from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Header, Input, Footer, Static, Markdown
from textual.containers import VerticalScroll
from textual.timer import Timer
from fetch_api import send_prompt
import os

class Prompt(Static):
    def __init__(self, message: str) -> None:
        super().__init__(f"> {message}", classes="user-message")

class Response(Markdown):
    pass

class Spinner(Static):
    SPINNER = ("⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏")

    def __init__(self) -> None:
        super().__init__(self.SPINNER[0], classes="spinner")
        self._index = 0
        self._timer: Timer | None = None

    def on_mount(self) -> None:
        """Start the spinner animation when the widget is mounted."""
        self._timer = self.set_interval(0.1, self._update_spinner)

    def _update_spinner(self) -> None:
        """Cycle through the spinner characters."""
        self._index = (self._index + 1) % len(self.SPINNER)
        self.update(self.SPINNER[self._index])

    def on_unmount(self) -> None:
        """Stop the timer when the widget is removed."""
        if self._timer:
            self._timer.stop()
            self._timer = None

class FourTCLIDemo(App):
    CSS = """
    .ascii-art {
        padding-left: 2;
        padding-right: 1;
        padding-top: 1;
        padding-bottom: 1;
        color: $text;
        text-align: left;
    }
    .tips {
        padding-left: 2;
        padding-right: 1;
        padding-top: 1;
        padding-bottom: 1;
        color: $text 70%;
        text-align: left;
    }
    #user-input {
        height: 3;
        padding: 0 2;
        border: round $primary;
        margin: 1 2;
        background: $background;
    }
    #user-input:focus {
        background: $background !important;
    }
    #model-label {
        padding-left: 2;
        padding-bottom: 1;
        color: $text 50%;
    }
    .user-message {
        padding-left: 2;
        padding-right: 1;
        padding-top: 1;
        padding-bottom: 1;
        color: $text 50%;
    }
    Response {
        padding-left: 2;
        padding-right: 1;
        padding-top: 1;
        padding-bottom: 1;
        background: $background;
        border: none;
        max-width: 80;  /* Ensure images don't overflow */
    }
    VerticalScroll {
        scrollbar-size: 0 0;  /* Hide scrollbar but keep scrolling */
    }
    .spinner {
        height: 1;
        width: 3;
        margin-left: 2;
        padding: 0;
        color: $primary;
        content-align: left middle;
        background: $background;
    }  /* Compact spinner */
    """

    AUTO_FOCUS = "Input"

    def compose(self) -> ComposeResult:
        ASCII_ART = r"""
██╗      ██╗  ██╗████████╗     ██████╗██╗     ██╗
╚██╗     ██║  ██║╚══██╔══╝    ██╔════╝██║     ██║
 ╚██╗    ███████║   ██║       ██║     ██║     ██║
 ██╔╝    ╚════██║   ██║       ██║     ██║     ██║
██╔╝          ██║   ██║       ╚██████╗███████╗██║
╚═╝           ╚═╝   ╚═╝        ╚═════╝╚══════╝╚═╝
"""
        TIPS = """
Tips:
- Use `/image {description}` to generate an image (e.g., `/image A sunset over a mountain`).
- Use `/inpaint {image_path} {description}` to modify an image (e.g., `/inpaint /path/to/image.png Add a rainbow`).
- Type any text for a regular query (e.g., `What is the capital of France?`).
"""
        with VerticalScroll(id="chat-view"):
            yield Static(ASCII_ART, classes="ascii-art")
            yield Static(TIPS, classes="tips")
        yield Input(placeholder="Hỏi 4T hoặc dùng /image hoặc /inpaint", id="user-input")
        yield Static("Model: 4T-Small", id="model-label")
        yield Footer()

    @on(Input.Submitted)
    async def on_input(self, event: Input.Submitted) -> None:
        chat_view = self.query_one("#chat-view")
        user_input = event.value.strip()
        event.input.clear()

        if not user_input:
            return

        # Mount user prompt
        await chat_view.mount(Prompt(user_input))

        # Create and mount a new Response widget
        response = Response()
        await chat_view.mount(response)
        response.anchor()

        # Mount spinner below the response
        spinner = Spinner()
        await chat_view.mount(spinner)

        # Parse input for commands
        if user_input.startswith("/image "):
            prompt = user_input[7:].strip()  # Extract prompt after "/image "
            if not prompt:
                await chat_view.mount(Response("❌ Vui lòng cung cấp yêu cầu tạo ảnh."))
                await spinner.remove()
                return
            send_prompt(self, prompt=prompt, is_image=True, response=response, loading=spinner)
        elif user_input.startswith("/inpaint "):
            parts = user_input[9:].strip().split(maxsplit=1)  # Split into image_path and prompt
            if len(parts) < 2:
                await chat_view.mount(Response("❌ Vui lòng cung cấp đường dẫn ảnh và yêu cầu tạo ảnh."))
                await spinner.remove()
                return
            image_path, prompt = parts
            if not os.path.exists(image_path):
                await chat_view.mount(Response(f"❌ File không tồn tại: {image_path}"))
                await spinner.remove()
                return
            send_prompt(self, prompt=prompt, is_inpaint=True, image_path=image_path, response=response, loading=spinner)
        else:
            send_prompt(self, prompt=user_input, response=response, loading=spinner)
