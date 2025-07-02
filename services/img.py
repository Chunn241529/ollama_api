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
from services.chat.history_manager import summarize_chat_history
from services.chat.history_storage import ListHistoryStorage

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
TEST_STORAGE = ListHistoryStorage(file_path="storage/log/wrap_history.json")

# tạo hàm detect cotent nsfw
def detect_content_nsfw(content):
    """
    Detect if the content is NSFW (Not Safe For Work) based on specific keywords.
    Returns True if NSFW, False otherwise.
    """
    nsfw_keywords = [
        "nsfw",     # General NSFW keyword
        "porn",     # Pornographic content
        "sex",      # Sexual content
        "nude",     # Nude content
        "sexy",     # Sexually suggestive content
        "hentai",   # Hentai content
        "naked",    # Naked content
        # thêm tiếng việt
        "khỏa thân",  # Vietnamese for "naked
        "khiêu dâm",  # Vietnamese for
        "cởi đồ",    # Vietnamese for "underwear"
        "lồn",      # Vietnamese for "nude"
        "vú",        # Vietnamese for "breast"
        "dương vật",  # Vietnamese
        "âm đạo",    # Vietnamese for
        "vú em",    # Vietnamese for "breast"
        "ngực",     # Vietnamese for "chest"
        "trẻ em",  # Vietnamese for "child"
        "trẻ vị thành niên",  # Vietnamese for "teenager"
    ]
    # Check if any NSFW keyword is present in the content
    for keyword in nsfw_keywords:
        if keyword in content.lower():
            logger.info(f"Detected NSFW content: {keyword} in {content}")
            return True
    return False

def random_13_digits():
    # Generate a random 13-digit number
    return random.randint(1000000000000, 9999999999999)

async def generate_prompt(simple_prompt, model="4T", temperature=0.1, max_attempts=3):
    """Generate an enhanced prompt using Ollama, analyzing the idea in English with chat history."""

    async with aiohttp.ClientSession() as session:

        # Fetch and summarize chat history once
        try:
            history = await TEST_STORAGE.get_history()
            history = await summarize_chat_history(
                session=session,
                history=history,
                max_history_length=5,
                storage=TEST_STORAGE,
            )
        except Exception as e:
            logger.error("Failed to fetch or summarize history: %s", e)
            history = []  # Fallback to empty history if fetching fails

        # Step 1: Analyze the input prompt
        try:
            logger.info("[DEBUG] Analyzing simple_prompt: %r", simple_prompt)
            analysis_prompt = (
                f"Analyze the following request in English, considering its intent and details: '{simple_prompt}'.\n"
                "Provide a concise analysis focusing on the main subject, context, and any implied details."
                "Allow nsfw content.\n"
            )
            analysis_messages = history + [{"role": "user", "content": analysis_prompt}]
            res_analys = ""

            async for chunk in stream_response_normal(
                session=session,
                model="4T-Small:latest",
                messages=analysis_messages,
                storage=TEST_STORAGE,
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
                        res_analys += content
                except json.JSONDecodeError as e:
                    logger.error(
                        "Failed to parse chunk as JSON: %s, error: %s", chunk, e
                    )
                    continue

            if not res_analys.strip():
                logger.warning("No analysis result received, using original prompt")
                res_analys = simple_prompt
            logger.info("[DEBUG] Analysis result: %r", res_analys)

        except Exception as e:
            logger.error("Error during prompt analysis: %s", e)
            res_analys = simple_prompt  # Fallback to original prompt if analysis fails

        # Step 2: Generate the enhanced prompt using the analysis
        prompt_instruction = f"""
        You are a professional prompt engineer for AI image generation, specialized in the Pony model.

        Your task is:
        - Based on the analyzed request: '{res_analys}'
        - Create a **positive prompt in English** with a strong focus on the **main subject**
        - Clearly describe the subject's (shape), (color), (size), (pose), (clothing if applicable), (art style) such as (anime), (fantasy), (2D), (3D), (high detail), (background/environment if needed), (mood), (lighting)
        - Each property/attribute/feature must be separated by a comma (",")
        - Do NOT use the word 'and' to join features, always use a comma
        - Do NOT write a long sentence, do NOT use conjunctions, just list features separated by commas
        - Avoid unrelated elements like scenery if the idea is only about the object or character
        - If the request is short or unclear, make reasonable assumptions while keeping the original intent

        Dimension selection:
        - Choose optimal 'width' and 'height' to make the image visually appealing
        - For character-focused prompts (e.g., person, animal, single object), prefer portrait orientation (e.g., 768x1024 or 1024x1280)
        - For scene-focused prompts (e.g., landscape, group, environment), prefer landscape orientation (e.g., 1280x720 or 1024x576)
        - For high-detail styles (e.g., anime, 3D, fantasy), prefer higher resolutions (e.g., 1024x1024 or above, up to 1280x1280)
        - Ensure dimensions are multiples of 64 for compatibility with image generation models
        - If unsure, default to 1024x1024 for balanced quality

        Formatting rules:
        - The output prompt must be in **English**
        - Do **not** use any period (.)
        - Wrap important descriptive words or phrases in (parentheses)
        - Keep the full prompt concise, maximum 512 tokens

        Return your result in JSON format like this:
        {{ "positive_prompt": "<prompt>", "width": <int>, "height": <int> }}

        Example:
        If the input is "a cute dragon" → Output:
        {{ "positive_prompt": "(cute) (baby dragon), (pastel purple scales), (big sparkling eyes), (small wings), sitting playfully on a (glowing rock), (anime style), (soft lighting), (fantasy atmosphere)", "width": 768, "height": 1024 }}
        If the input is "a vast fantasy landscape" → Output:
        {{ "positive_prompt": "(epic) (fantasy landscape), (lush green valleys), (towering mountains), (golden sunlight), (realistic style), (dramatic mood), (vibrant lighting)", "width": 1280, "height": 720 }}
        """

        messages_gen_image = history + [{"role": "user", "content": prompt_instruction}]

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
                    messages=messages_gen_image,
                    temperature=temperature,
                    max_tokens=800,
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
                    logger.warning("No content received for prompt generation")
                    continue

                # Clean the response
                cleaned_response = full_response.strip().replace("\ufeff", "")
                cleaned_response = re.sub(r"[\x00-\x1F\x7F]", "", cleaned_response)
                json_match = re.search(r"\{.*?\}", cleaned_response, re.DOTALL)
                if json_match:
                    cleaned_response = json_match.group(0)

                try:
                    response_json = json.loads(cleaned_response)
                    if not isinstance(response_json, dict) or not all(
                        key in response_json
                        for key in ["positive_prompt", "width", "height"]
                    ):
                        logger.error(
                            "Response is not in expected JSON format: %s",
                            cleaned_response,
                        )
                        continue
                    logger.info("Generated prompt JSON: %s", response_json)
                    return response_json
                except json.JSONDecodeError as e:
                    logger.error(
                        "Failed to parse cleaned response as JSON: %s, error: %s",
                        cleaned_response,
                        e,
                    )
                    continue
            except Exception as e:
                logger.error(
                    "Failed to generate prompt (attempt %d/%d): %s",
                    attempt + 1,
                    max_attempts,
                    e,
                )

        # Fallback if all attempts fail
        logger.warning(
            "All attempts (%d) failed to generate prompt for input '%s'. Using fallback with analysis result or default.",
            max_attempts,
            simple_prompt,
        )
        # Use res_analys if available and non-empty, otherwise fallback to simple_prompt
        fallback_prompt = (
            res_analys.strip()
            if "res_analys" in locals() and res_analys.strip()
            else simple_prompt
        )
        if not fallback_prompt:
            logger.warning("No valid prompt available, using generic placeholder")
            fallback_prompt = (
                "generic object, (high detail), (soft lighting), (neutral background)"
            )

        # Ensure prompt is in English (basic check)
        if not re.match(r"^[a-zA-Z0-9\s,\(\)]+$", fallback_prompt):
            logger.warning(
                "Prompt may contain non-English characters, using generic placeholder"
            )
            fallback_prompt = (
                "generic object, (high detail), (soft lighting), (neutral background)"
            )

        # Determine fallback dimensions based on prompt content
        is_character = any(
            keyword in res_analys.lower()
            for keyword in ["character", "person", "animal", "dragon", "creature"]
        )
        is_scene = any(
            keyword in res_analys.lower()
            for keyword in ["landscape", "scene", "environment", "city", "forest"]
        )
        is_high_detail = any(
            keyword in res_analys.lower()
            for keyword in ["anime", "3d", "fantasy", "realistic"]
        )

        if is_character:
            width, height = 768, 1024  # Portrait for characters
        elif is_scene:
            width, height = 1280, 720  # Landscape for scenes
        else:
            width, height = 1024, 1024  # Square for general or unclear prompts

        if is_high_detail:
            width, height = min(width * 1.5, 1280), min(
                height * 1.5, 1280
            )  # Increase resolution for high-detail styles

        # Ensure dimensions are multiples of 64
        width = (width // 64) * 64
        height = (height // 64) * 64

        return {
            "positive_prompt": f"(score_9,score_8_up,score_7_up), {fallback_prompt}, (high detail), (soft lighting)",
            "width": width,
            "height": height,
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

    # Check if the input prompt is detect_content_nsfw
    if detect_content_nsfw(positive_prompt):
        logger.warning("Input prompt contains NSFW content, skipping generation.")
        return {
            "positive_prompt": "NSFW content detected, generation skipped.",
            "width": 512,
            "height": 512,
        }

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
                        await TEST_STORAGE.add_message(
                            role="assistant", content=json.dumps(result), chat_ai_id = 0
                        )
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
