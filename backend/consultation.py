import time
from typing import Dict, List, Optional
from pydantic import BaseModel


# --- DATA MODELS ---
class MessageItem(BaseModel):
    role: str = "models"  # 'user' or 'models'
    text: str
    facialExpression: Optional[str] = "smile"
    animation: Optional[str] = "Idle"
    audio: Optional[str] = None
    lipsync: Optional[dict] = None


# --- IN-MEMORY DATABASE ---
# Structure: { "chat_id": { "id": "...", "title": "...", "messages": [], "report": None } }
_consultations: Dict[str, dict] = {}


class ConsultationManager:
    """
    Manages the lifecycle of chat sessions (create, get, delete, add messages).
    """

    @staticmethod
    def get_all_summaries():
        """Returns a list of all consultations (id and title only)."""
        return [{"id": c["id"], "title": c["title"]} for c in _consultations.values()]

    @staticmethod
    def create_chat():
        """Creates a new empty consultation session."""
        chat_id = str(int(time.time()))
        title = f"Consultation {len(_consultations) + 1}"
        new_chat = {
            "id": chat_id,
            "title": title,
            "messages": [],
            "report": None
        }
        _consultations[chat_id] = new_chat
        return new_chat

    @staticmethod
    def get_chat(chat_id: str):
        """Returns full details of a chat or None if not found."""
        return _consultations.get(chat_id)

    @staticmethod
    def delete_chat(chat_id: str):
        """Deletes a chat session."""
        if chat_id in _consultations:
            del _consultations[chat_id]
            return True
        return False

    @staticmethod
    def add_message(chat_id: str, role: str, text: str, audio: str = None, lipsync: dict = None):
        """Adds a message to the consultation history."""
        if chat_id not in _consultations:
            return False

        msg_entry = {
            "role": role,
            "text": text,
            "audio": audio,
            "lipsync": lipsync
        }
        _consultations[chat_id]["messages"].append(msg_entry)

        # Auto-update title if it's the first user message
        if role == "user" and len(_consultations[chat_id]["messages"]) <= 2:
            _consultations[chat_id]["title"] = text[:30] + ("..." if len(text) > 30 else "")

        return True