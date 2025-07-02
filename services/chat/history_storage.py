import json
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, List

from services.repository.repo_client import RepositoryClient

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)



class HistoryStorage(ABC):
    @abstractmethod
    async def add_message(self, role: str, content: str, chat_ai_id: int = None) -> None:
        pass

    @abstractmethod
    async def get_history(self, chat_ai_id: int = None) -> List[Dict[str, str]]:
        pass

    @abstractmethod
    async def clear_history(self, chat_ai_id: int = None) -> None:
        pass

class DatabaseHistoryStorage(HistoryStorage):
    def __init__(self, repo_client):
        self.repo_client = repo_client

    async def add_message(self, role: str, content: str, chat_ai_id: int = None) -> None:
        if chat_ai_id is None:
            raise ValueError("chat_ai_id is required for DatabaseHistoryStorage")
        try:
            logger.debug(f"Adding message to database - chat_ai_id: {chat_ai_id}, role: {role}")
            self.repo_client.insert_brain_history_chat(chat_ai_id, role, content)
            logger.debug("Successfully added message to database")
        except Exception as e:
            logger.error(f"Error adding message to database: {str(e)}")
            raise

    async def get_history(self, chat_ai_id: int = None) -> List[Dict[str, str]]:
        if chat_ai_id is None:
            raise ValueError("chat_ai_id is required for DatabaseHistoryStorage")
        try:
            logger.debug(f"Fetching history for chat_ai_id: {chat_ai_id}")
            history = self.repo_client.get_brain_history_chat_by_chat_ai_id(chat_ai_id)
            logger.debug(f"Found {len(history)} messages in history")
            return [{"role": row[0], "content": row[1]} for row in history]
        except Exception as e:
            logger.error(f"Error fetching history from database: {str(e)}")
            return []

    async def clear_history(self, chat_ai_id: int = None) -> None:
        if chat_ai_id is None:
            raise ValueError("chat_ai_id is required for DatabaseHistoryStorage")
        try:
            logger.debug(f"Clearing history for chat_ai_id: {chat_ai_id}")
            self.repo_client.delete_brain_history_chat(chat_ai_id)
            logger.debug(f"Successfully cleared history for chat_ai_id {chat_ai_id}")
        except Exception as e:
            logger.error(f"Error clearing history from database: {str(e)}")
            raise

class ListHistoryStorage(HistoryStorage):
    def __init__(self, file_path="storage/log/wrap_history.json"):
        self.file_path = file_path
        self.history = self._load_history()
        self.lock = asyncio.Lock()

    def _load_history(self):
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            return []

    def _save_history(self):
        try:
            with open(self.file_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Error saving history to {self.file_path}: {str(e)}")

    async def add_message(self, role: str, content: str, chat_ai_id: int = None) -> None:
        recent_history = self.history[-10:] if len(self.history) > 10 else self.history
        for msg in recent_history:
            if msg.get("role") == role and msg.get("content") == content:
                return

        async with self.lock:
            self.history.append({"role": role, "content": content})
            self._save_history()

    async def get_history(self, chat_ai_id: int = None) -> List[Dict[str, str]]:
        logger.debug(f"Fetching list history: {len(self.history)} messages")
        return self.history

    async def clear_history(self, chat_ai_id: int = None) -> None:
        async with self.lock:
            self.history.clear()
            self._save_history()
            logger.debug("Cleared list history")
