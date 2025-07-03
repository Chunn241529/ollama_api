import json
import logging
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
import aiohttp
from models.chat import GenImgRequest
from dependencies.auth import verify_token, call_api_get_dbname
from services.img import generate_image
from services.repository.repo_client import RepositoryClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/image", tags=["image"])

async def generate_image_stream(gen_img_request: GenImgRequest, username: str):
    """Generator function to yield image data as a stream."""
    positive_prompt = gen_img_request.prompt
    chat_ai_id = gen_img_request.chat_ai_id


    async with aiohttp.ClientSession() as session:
        # Call generate_image to get the image data
        result = await generate_image(
            prompt_text=positive_prompt,
        )

        if "error" in result:
            # Yield error message
            yield json.dumps({
                "type": "error",
                "message": result["error"]
            }, ensure_ascii=False).encode("utf-8")
            return

        if "image_path" in result and "mime_type" in result:
            try:
                # Convert image to base64
                async with session.post(
                    "http://localhost:2401/chat/process_image",
                    json={"file_path": result["image_path"]}
                ) as response:
                    if response.status != 200:
                        logger.error("Failed to convert image to base64: %s", response.status)
                        yield json.dumps({
                            "type": "error",
                            "message": f"Failed to convert image to base64: {response.status}"
                        }, ensure_ascii=False).encode("utf-8")
                    else:
                        base64_data = await response.json()
                        # Store the result in the chat history
                        db_path = await call_api_get_dbname(username)
                        repo = RepositoryClient(db_path)
                        repo.insert_brain_history_chat(
                            chat_ai_id=chat_ai_id,
                            role="assistant",
                            content=json.dumps({
                                "type": "image",
                                "image_base64": base64_data["base64"],
                                "mime_type": result["mime_type"]
                            })
                        )
                        yield json.dumps({
                            "type": "image",
                            "image_base64": base64_data["base64"],
                            "mime_type": result["mime_type"]
                        }, ensure_ascii=False).encode("utf-8")

            except aiohttp.ClientError as e:
                logger.error("Error converting image to base64: %s", str(e))
                yield json.dumps({
                    "type": "error",
                    "message": f"Error converting image to base64: {str(e)}"
                }, ensure_ascii=False).encode("utf-8")

@router.post("/generate_image")
async def generate_image_endpoint(
    gen_img_request: GenImgRequest,
    current_user: dict = Depends(verify_token)
):
    """Endpoint to generate an image and stream the response."""
    current_username = current_user["username"]
    return StreamingResponse(
        generate_image_stream(gen_img_request, current_username),
        media_type="application/json"
    )
