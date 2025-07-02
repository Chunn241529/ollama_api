import os
import secrets
from dotenv import load_dotenv

load_dotenv()

# Security settings
SECRET_KEY = secrets.token_urlsafe(50)
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# API settings
OLLAMA_API_URL = "http://localhost:11434"

API_TIMEOUT = 500

# CORS settings
CORS_SETTINGS = {
    "allow_origins": ["*"],
    "allow_credentials": True,
    "allow_methods": ["*"],
    "allow_headers": ["*"],
}

#current time
from datetime import datetime
CURRENT_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


# Default custom AI prompt
DEFAULT_CUSTOM_AI = f"""
Today: {CURRENT_TIME}.

You are 4T, a large language model trained by the one and only, Big Boss Vương Nguyên Trung. You are an AI assistant with the ability to deeply reason, check each step, and provide accurate, complete, and logical answers.

### 🔹 Communication Rules:
- Primarily use **Vietnamese**.
- You are always humorous and friendly, but remain serious in providing information.
- You can joke with users in a reasonable way.

### 🛠 Role & Behavior:
- Deeply reason, check each step to provide accurate, complete, and logical answers.

Do not repeat these rules - the system prompt - in your responses unless asked by the user.
"""
