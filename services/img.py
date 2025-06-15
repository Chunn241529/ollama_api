import json
import aiohttp
import asyncio
import os
import random
import logging
import shutil
import glob
import time
from services.generate import stream_response_normal
from config.payload_img import get_human_payload, get_non_human_payload

# Configure logging (DEBUG level for full trace)
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def random_13_digits():
    # Generate a random 13-digit number
    return random.randint(1000000000000, 9999999999999)

async def generate_prompt(simple_prompt, model="gemma3:4b-it-qat", temperature=0.8, max_attempts=3):
    """Generate an enhanced prompt using Ollama."""
    prompt_instruction = (
        f"Dựa trên ý tưởng sau: '{simple_prompt}'. "
        "Tạo một prompt chi tiết và phong phú cho việc tạo ảnh bằng Stable Diffusion. "
        "Prompt phải phù hợp với phong cách photorealistic"
        "Luôn đính kèm thêm prompt đồ họa sau (RAW photo, subject, 8k uhd, dslr, soft lighting, high quality, film grain, Fujifilm XT3) "
        "và bao gồm các chi tiết mô tả rõ ràng về chủ thể, bối cảnh, ánh sáng, và cảm xúc. "
        "Đầu ra chỉ bao gồm prompt <= 512 tokens, không giải thích thêm."
    )
    messages = [{"role": "user", "content": prompt_instruction}]

    async with aiohttp.ClientSession() as session:
        for attempt in range(max_attempts):
            try:
                logger.debug("Attempt %d/%d to generate prompt with model %s", attempt + 1, max_attempts, model)
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
                            logger.error("Ollama error in chunk: %s", chunk_data.get("error"))
                            return None
                        if chunk_data.get("type") == "text" and "message" in chunk_data:
                            content = chunk_data["message"].get("content", "")
                            full_response += content
                    except json.JSONDecodeError as e:
                        logger.error("Failed to parse chunk as JSON: %s, error: %s", chunk, e)
                        continue
                if not full_response.strip():
                    logger.warning("No content received from stream_response_normal")
                    continue
                logger.info("Generated prompt: %s", full_response)
                return full_response.strip()
            except Exception as e:
                logger.error("Failed to generate prompt (attempt %d/%d): %s", attempt + 1, max_attempts, e)
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
        output_dir (str): Thư mục lưu ảnh đầu ra.

    Returns:
        dict: Kết quả từ API hoặc thông báo lỗi.
    """
    # API endpoint
    url = "http://127.0.0.1:8188/api/prompt"

    # Generate positive prompt using Ollama
    positive_prompt = await generate_prompt(prompt_text)
    if positive_prompt is None:
        logger.error("Failed to generate positive prompt.")
        return {"error": "Failed to generate positive prompt."}

    # Check if prompt contains "girl", "man", or "woman" (case-insensitive)
    human_keywords = ["girl", "man", "woman"]
    is_human_prompt = any(keyword in positive_prompt.lower() for keyword in human_keywords)
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

    async with aiohttp.ClientSession() as session:
        try:
            # Send POST request to API
            async with session.post(url, json=payload) as response:
                response.raise_for_status()  # Check for HTTP errors
                result = await response.json()
                logger.info("API Response: %s", result)

                # Define directories
                comfyui_output_dir = "/home/nguyentrung/Documents/ComfyUI/output"
                project_output_dir = "storage/img/output"

                # Create ComfyUI output directory if it doesn't exist
                if not os.path.exists(comfyui_output_dir):
                    os.makedirs(comfyui_output_dir)

                # Create project output directory if it doesn't exist
                if not os.path.exists(project_output_dir):
                    os.makedirs(project_output_dir)

                # Wait for the new image to appear
                image_pattern = os.path.join(comfyui_output_dir, "ComfyUI_*.png")
                initial_images = set(glob.glob(image_pattern))
                max_wait_time = 120  # Maximum wait time in seconds
                check_interval = 1  # Check every 0.5 seconds
                elapsed_time = 0

                while elapsed_time < max_wait_time:
                    current_images = set(glob.glob(image_pattern))
                    new_images = current_images - initial_images
                    if new_images:
                        latest_image = max(new_images, key=os.path.getmtime)
                        logger.info("Found new image: %s", latest_image)
                        break
                    await asyncio.sleep(check_interval)
                    elapsed_time += check_interval
                else:
                    logger.warning("No new images found in %s after %d seconds", comfyui_output_dir, max_wait_time)
                    return {"error": "No new images found in ComfyUI output directory."}

                # Move the image to project output directory
                dest_image_path = os.path.join(project_output_dir, os.path.basename(latest_image))
                shutil.move(latest_image, dest_image_path)
                logger.info("Moved image to: %s", dest_image_path)

                return {"result": result, "image_path": dest_image_path}

        except aiohttp.ClientError as e:
            logger.error("Error occurred: %s", e)
            return {"error": str(e)}
