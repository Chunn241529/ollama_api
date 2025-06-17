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
from services.generate import stream_response_normal
from config.payload_img import get_human_payload, get_non_human_payload

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
    simple_prompt, model="gemma3:4b-it-qat", temperature=0.4, max_attempts=3
):
    """Generate an enhanced prompt using Ollama."""
    prompt_instruction = (
        f"Dựa trên ý tưởng sau: '{simple_prompt}'. "
        "Tạo một prompt chi tiết và phong phú cho việc tạo ảnh bằng Stable Diffusion. "
        "Prompt phải phù hợp với phong cách photorealistic. "
        "Luôn đính kèm thêm prompt đồ họa sau (RAW photo, subject, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT3) "
        "và bao gồm các chi tiết mô tả rõ ràng về chủ thể, bối cảnh, ánh sáng, và cảm xúc. "
        "Đầu ra chỉ bao gồm prompt <= 512 tokens, không giải thích thêm."
    )
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
                logger.info("Generated prompt: %s", full_response)
                return full_response.strip()
            except Exception as e:
                logger.error(
                    "Failed to generate prompt (attempt %d/%d): %s",
                    attempt + 1,
                    max_attempts,
                    e,
                )
                if attempt == max_attempts - 1:
                    return None
    return None


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

    # Generate positive prompt using Ollama
    positive_prompt = await generate_prompt(prompt_text)
    if positive_prompt is None:
        logger.error("Failed to generate positive prompt.")
        return {"error": "Failed to generate positive prompt."}

    # Check if prompt contains "girl", "man", or "woman" (case-insensitive)
    human_keywords = ["girl", "man", "woman"]
    is_human_prompt = any(
        keyword in positive_prompt.lower() for keyword in human_keywords
    )
    logger.info("Prompt contains human keywords: %s", is_human_prompt)

    # Get payloads
    human_payload = get_human_payload(
        positive_prompt=positive_prompt,
        width=width,
        height=height,
    )
    non_human_payload = get_non_human_payload(
        positive_prompt=positive_prompt,
        width=width,
        height=height,
    )

    # Select payload based on prompt content
    payload = human_payload if is_human_prompt else non_human_payload
    logger.info("Payload sent to ComfyUI: %s", json.dumps(payload, indent=2))

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
                        shutil.copy2(latest_image, storage_path)
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
