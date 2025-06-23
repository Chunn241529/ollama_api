import json
import aiohttp
import asyncio
import os
import random
import logging
import glob
import time
import base64
import re
import shutil
from datetime import datetime

import requests
from services.chat import stream_response_normal
from config.payload_img import get_payload

# Configure logging (DEBUG level for full trace)
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# Define output directories
STORAGE_OUTPUT_DIR = os.path.abspath("storage/img/output")
COMFY_OUTPUT_DIR = os.path.abspath("modules/ComfyUI/output")


def random_13_digits():
    # Generate a random 13-digit number
    return random.randint(1000000000000, 9999999999999)


async def generate_prompt(
    simple_prompt, model="gemma3:12b-it-q4_K_M", temperature=0.4, max_attempts=3
):
    """Generate an enhanced prompt using Ollama, with an extra step to analyze the idea in English first."""

    prompt_instruction = f"""
        Dựa trên yêu cầu: '{simple_prompt}'.
        Tạo một positive prompt chi tiết để vẽ hình ảnh sử dụng model Pony, tập trung vào đối tượng chính của ý tưởng.
        Positive prompt rõ ràng các đặc điểm của đối tượng chính bao gồm hình dáng, màu sắc, kích thước, tư thế, và phong cách nghệ thuật (ví dụ: anime, fantasy, 2d, 3d, chi tiết cao).
        Chỉ thêm bối cảnh hoặc môi trường nếu nó làm nổi bật đối tượng chính, tránh đưa vào các yếu tố không liên quan (như phong cảnh nếu ý tưởng chỉ nói về đối tượng).
        Xác định tâm trạng (ví dụ: hùng vĩ, bí ẩn, dữ tợn) và ánh sáng (ví dụ: rực rỡ, mờ ảo) để tăng tính hấp dẫn.
        Nếu yêu cầu ngắn gọn hoặc không rõ ràng, suy ra chi tiết hợp lý nhưng vẫn bám sát ý tưởng gốc.
        Positive prompt phải ngắn gọn, tối đa 300 token, nhưng đầy đủ để tạo hình ảnh chất lượng cao.
        Trả về một JSON với các trường: {{'positive_prompt': str, 'width': int, 'height': int}}.
     """

    messages = [{"role": "user", "content": prompt_instruction}]
    async with aiohttp.ClientSession() as session:
        for attempt in range(max_attempts):
            try:
                logger.debug(
                    "Attempt %d/%d to generate prompt with model %s",
                    attempt + 1,
                    max_attempts,
                    model,
                )
                full_response = ""
                async for chunk in stream_response_normal(
                    session,
                    model,
                    messages,
                    temperature=temperature,
                ):
                    try:
                        chunk_data = json.loads(chunk.strip())
                        if chunk_data.get("type") == "error":
                            logger.error(
                                "Ollama error in chunk: %s", chunk_data.get("error")
                            )
                            return None
                        if chunk_data.get("type") == "text" and "message" in chunk_data:
                            content = chunk_data["message"].get("content", "")
                            full_response += content
                    except json.JSONDecodeError as e:
                        logger.error(
                            "Failed to parse chunk as JSON: %s, error: %s", chunk, e
                        )
                        continue
                if not full_response.strip():
                    logger.warning("No content received from stream_response_normal")
                    continue
                # Log raw response for debugging
                # logger.debug("Raw response: %r", full_response)
                # Clean the response: remove BOM, control characters, and extra whitespace
                cleaned_response = full_response.strip()
                cleaned_response = cleaned_response.replace('\ufeff', '')  # Remove BOM
                cleaned_response = re.sub(r'[\x00-\x1F\x7F]', '', cleaned_response)  # Remove control characters
                # Try to extract JSON using regex if direct parsing fails
                json_match = re.search(r'\{.*?\}', cleaned_response, re.DOTALL)
                if json_match:
                    cleaned_response = json_match.group(0)
                    # logger.debug("Extracted JSON-like string: %s", cleaned_response)
                # Try to parse the cleaned response as JSON
                try:
                    response_json = json.loads(cleaned_response)
                    if not isinstance(response_json, dict) or not all(
                        key in response_json for key in ["positive_prompt", "width", "height"]
                    ):
                        logger.error("Response is not in expected JSON format: %s", cleaned_response)
                        continue
                    # logger.info("Generated prompt JSON: %s", response_json)
                    return response_json
                except json.JSONDecodeError as e:
                    logger.error("Failed to parse cleaned response as JSON: %s, error: %s", cleaned_response, e)
                    continue
            except Exception as e:
                logger.error(
                    "Failed to generate prompt (attempt %d/%d): %s",
                    attempt + 1,
                    max_attempts,
                    e,
                )
                if attempt == max_attempts - 1:
                    # Fallback to default values if all attempts fail
                    logger.warning("All attempts failed, returning default prompt")
                    return {
                        "positive_prompt": (
                            f"(score_9,score_8_up,score_7_up), {simple_prompt}"
                        ),
                        "width": 768,
                        "height": 1024
                    }
    # Fallback if all attempts fail
    logger.error("Failed to generate prompt after %d attempts", max_attempts)
    return {
        "positive_prompt": (
            f"(score_9,score_8_up,score_7_up), {simple_prompt}"
        ),
        "width": 768,
        "height": 1024
    }


async def generate_image(prompt_text="", width=768, height=1024, output_dir="ComfyUI"):
    """
    Hàm tạo ảnh sử dụng API ComfyUI với payload.

    Args:
        prompt_text (str): Mô tả tích cực cho ảnh (ví dụ: "a cute cat").
        width (int): Chiều rộng ảnh.
        height (int): Chiều cao ảnh.
        output_dir (str): Thư mục lưu ảnh đầu ra (không sử dụng, giữ cho tương thích).

    Returns:
        dict: {"image_url": str, "image_path": str, "mime_type": str} hoặc {"error": str} nếu có lỗi.
    """
    # API endpoint
    url = "http://127.0.0.1:8188/api/prompt"
    base_url = "http://localhost:2401"  # Base URL cho image_url

    # Generate prompt using Ollama
    prompt_data = await generate_prompt(prompt_text)
    if prompt_data is None:
        logger.error("Failed to generate prompt data.")
        return {"error": "Failed to generate prompt data."}

    # Extract values from prompt_data
    positive_prompt = prompt_data.get("positive_prompt")
    width = prompt_data.get("width", width)  # Use provided width as fallback
    height = prompt_data.get("height", height)  # Use provided height as fallback

    if not positive_prompt:
        logger.error("No positive prompt extracted from response.")
        return {"error": "No positive prompt extracted from response."}

    # Get payload
    payload = get_payload(
        positive_prompt=positive_prompt,
        width=width,
        height=height,
    )

    async with aiohttp.ClientSession() as session:
        try:
            # Check ComfyUI output directory
            if not os.path.exists(COMFY_OUTPUT_DIR):
                logger.error(
                    "ComfyUI output directory does not exist: %s", COMFY_OUTPUT_DIR
                )
                return {
                    "error": f"ComfyUI output directory {COMFY_OUTPUT_DIR} does not exist."
                }
            if not os.access(COMFY_OUTPUT_DIR, os.R_OK | os.W_OK):
                logger.error(
                    "No read/write permissions for directory: %s", COMFY_OUTPUT_DIR
                )
                return {"error": f"No read/write permissions for {COMFY_OUTPUT_DIR}."}

            # Check storage output directory
            if not os.path.exists(STORAGE_OUTPUT_DIR):
                os.makedirs(STORAGE_OUTPUT_DIR)
            if not os.access(STORAGE_OUTPUT_DIR, os.R_OK | os.W_OK):
                logger.error(
                    "No read/write permissions for directory: %s", STORAGE_OUTPUT_DIR
                )
                return {"error": f"No read/write permissions for {STORAGE_OUTPUT_DIR}."}

            logger.info(
                "Checking output directories - ComfyUI: %s, Storage: %s",
                COMFY_OUTPUT_DIR,
                STORAGE_OUTPUT_DIR,
            )

            # Send POST request to API
            start_time = time.time()
            async with session.post(url, json=payload) as response:
                response.raise_for_status()  # Check for HTTP errors
                result = await response.json()
                logger.info(
                    "API Response: %s, Time taken: %s seconds",
                    result,
                    time.time() - start_time,
                )

                # Wait for the new image to appear
                image_pattern = os.path.join(COMFY_OUTPUT_DIR, "*.*")
                initial_images = set(glob.glob(image_pattern))
                max_wait_time = max(300, min(600, (width * height) // 10000))
                check_interval = 0.5
                elapsed_time = 0

                while elapsed_time < max_wait_time:
                    current_images = set(glob.glob(image_pattern))
                    new_images = current_images - initial_images
                    if new_images:
                        # Filter valid image extensions
                        valid_extensions = {".png", ".jpg", ".jpeg", ".webp", ".bmp"}
                        new_images = {
                            img
                            for img in new_images
                            if os.path.splitext(img)[1].lower() in valid_extensions
                        }
                        if not new_images:
                            await asyncio.sleep(check_interval)
                            elapsed_time += check_interval
                            continue

                        # Extract sequence number from filenames
                        def get_sequence_number(image_path):
                            filename = os.path.basename(image_path)
                            match = re.search(r"(\d+)", filename)
                            return int(match.group(1)) if match else -1

                        # Select image with highest sequence number
                        latest_image = max(new_images, key=get_sequence_number)
                        sequence_number = get_sequence_number(latest_image)
                        if sequence_number == -1:
                            latest_image = max(new_images, key=os.path.getmtime)
                            logger.warning(
                                "No sequence number found, using most recent: %s",
                                latest_image,
                            )

                        # Create a unique filename with timestamp
                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                        ext = os.path.splitext(latest_image)[1].lower()
                        new_filename = f"img_{timestamp}_{random_13_digits()}{ext}"
                        storage_path = os.path.join(STORAGE_OUTPUT_DIR, new_filename)

                        # Copy the image to storage
                        shutil.move(latest_image, storage_path)
                        logger.info("Image copied to storage: %s", storage_path)

                        # Đặt quyền tệp
                        os.chmod(storage_path, 0o644)
                        if not os.access(storage_path, os.R_OK):
                            logger.error(
                                "No read permissions for image: %s", storage_path
                            )
                            return {"error": f"No read permissions for {storage_path}."}

                        # Generate absolute URL for the image
                        image_url = f"{base_url}/storage/img/output/{new_filename}"
                        mime_type = "jpeg" if ext in [".jpg", ".jpeg"] else ext[1:]

                        result = {
                            "image_url": image_url,
                            "image_path": storage_path,
                            "mime_type": f"image/{mime_type}",
                        }
                        logger.info("Returning image result: %s", result)
                        return result

                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval

                logger.warning(
                    "No new images found in %s after %d seconds",
                    COMFY_OUTPUT_DIR,
                    max_wait_time,
                )
                return {
                    "error": f"No new images found in {COMFY_OUTPUT_DIR} after {max_wait_time} seconds."
                }

        except aiohttp.ClientError as e:
            logger.error("Error occurred during API request: %s", e)
            return {"error": f"API request failed: {str(e)}"}
        except Exception as e:
            logger.error("Unexpected error: %s", e)
            return {"error": f"Unexpected error: {str(e)}"}
