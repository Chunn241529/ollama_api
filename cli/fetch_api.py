import httpx
import json
import base64
import tempfile
import subprocess
import os
from textual import work

API_URL = "http://localhost:2401/chat/test"

@work(thread=True)
def send_prompt(app, prompt: str, response, loading, is_image=False, is_inpaint=False, image_path=None) -> None:
    response_content = ""
    request_data = {
        "prompt": prompt,
        "model": "4T-Small:latest",
        "is_deep_think": False,
        "is_deepsearch": False,
        "is_image": is_image,
        "is_inpaint": is_inpaint
    }

    # If inpainting, read and encode the image file
    if is_inpaint and image_path:
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()
                image_base64 = base64.b64encode(image_data).decode("utf-8")
                request_data["image_base64"] = image_base64
                request_data["mime_type"] = "image/png"  # Assume PNG; adjust if needed
        except Exception as e:
            error_msg = f"\n❌ Lỗi khi đọc file ảnh: {str(e)}\n"
            app.call_from_thread(response.update, error_msg)
            print(f"File read error: {error_msg}")
            app.call_from_thread(lambda: app.query_one("#chat-view").scroll_to_widget(loading))
            app.call_from_thread(lambda: print("Removing spinner") or loading.remove())
            return

    try:
        with httpx.stream(
            "POST",
            API_URL,
            json=request_data,
            timeout=5000  # Add a timeout to avoid hanging
        ) as res:
            for line in res.iter_lines():
                if not line.strip():
                    continue
                print(f"Raw response line: {line}")  # Debug raw response
                try:
                    data = json.loads(line)
                    if not isinstance(data, dict):
                        error_msg = f"\n❌ Response is not a dictionary: {data}\n"
                        app.call_from_thread(response.update, error_msg)
                        print(error_msg)
                        continue
                    if "message" in data:
                        content = data["message"].get("content", "")
                        response_content += content
                        app.call_from_thread(response.update, response_content)
                        print(f"Text response: {content}")
                    elif data.get("type") == "error":
                        error_msg = f"\n❌ {data['message']}\n"
                        app.call_from_thread(response.update, error_msg)
                        print(f"Error response: {error_msg}")
                    elif data.get("type") == "image":
                        image_base64 = data.get("image_base64", "")
                        mime_type = data.get("mime_type", "image/png")
                        # Save image to temporary file and open with Firefox
                        image_data = base64.b64decode(image_base64)
                        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                            temp_file.write(image_data)
                            temp_file_path = temp_file.name
                        subprocess.run(["firefox", temp_file_path])
                        os.unlink(temp_file_path)  # Clean up
                        # Display the image in the UI
                        image_markdown = f"![Image](file://{temp_file_path})"
                        app.call_from_thread(response.update, image_markdown)
                        print(f"Image opened in Firefox: {temp_file_path}")
                    # Scroll to the spinner during loading
                    app.call_from_thread(lambda: app.query_one("#chat-view").scroll_to_widget(loading))
                except json.JSONDecodeError:
                    error_msg = f"\n⚠️ Invalid JSON line: {line}\n"
                    app.call_from_thread(response.update, error_msg)
                    print(f"JSON decode error: {error_msg}")
                    app.call_from_thread(lambda: app.query_one("#chat-view").scroll_to_widget(loading))
            # Scroll to the response after loading completes
            app.call_from_thread(lambda: app.query_one("#chat-view").scroll_to_widget(response))
    except httpx.ConnectTimeout:
        error_msg = "\n❌ Kết nối đến API bị từ chối: Vui lòng kiểm tra server đang chạy.\n"
        app.call_from_thread(response.update, error_msg)
        print(f"Connection timeout: {error_msg}")
        app.call_from_thread(lambda: app.query_one("#chat-view").scroll_to_widget(response))
    except Exception as e:
        error_msg = f"\n❌ Exception: {str(e)}\n"
        app.call_from_thread(response.update, error_msg)
        print(f"Exception: {error_msg}")
        app.call_from_thread(lambda: app.query_one("#chat-view").scroll_to_widget(response))
    finally:
        # Remove spinner and scroll to response
        app.call_from_thread(lambda: print("Removing spinner") or loading.remove())
        app.call_from_thread(lambda: app.query_one("#chat-view").scroll_to_widget(response))
