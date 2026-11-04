"""Tutor History Persistence Service for EduAdapt.

Provides student-specific, topic-isolated chat history management.
Ensures conversations survive navigation and page refresh, isolates discussions
per curriculum topic, and avoids cross-topic contamination.
"""

from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

HISTORY_FILE = Path(__file__).resolve().parent.parent.parent.parent / "data" / "tutor_history.json"


class TutorHistoryService:
    """Manages persistent chat history for the AI Tutor."""

    def __init__(self, history_file: Optional[Path] = None) -> None:
        self.history_file = history_file or HISTORY_FILE
        self._ensure_file()

    def _ensure_file(self) -> None:
        try:
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
            if not self.history_file.exists():
                self.history_file.write_text("{}", encoding="utf-8")
        except Exception:
            pass

    def _load(self) -> Dict[str, Any]:
        try:
            if self.history_file.exists():
                content = self.history_file.read_text(encoding="utf-8")
                return json.loads(content) if content.strip() else {}
        except Exception:
            pass
        return {}

    def _save(self, data: Dict[str, Any]) -> None:
        try:
            self.history_file.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception:
            pass

    def get_history(self, student_id: str, topic: str) -> List[Dict[str, Any]]:
        """Retrieve topic-specific chat history for a given student."""
        data = self._load()
        student_data = data.get(student_id, {})
        return student_data.get(topic, [])

    def append_message(
        self,
        student_id: str,
        topic: str,
        role: str,
        text: str,
        prompt_variation: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Append a message to the student's topic chat history."""
        data = self._load()
        if student_id not in data:
            data[student_id] = {}
        if topic not in data[student_id]:
            data[student_id][topic] = []

        entry = {
            "role": role,
            "text": text,
            "timestamp": datetime.now().isoformat(),
        }
        if prompt_variation:
            entry["prompt_variation"] = prompt_variation

        data[student_id][topic].append(entry)
        self._save(data)
        return entry

    def clear_topic_history(self, student_id: str, topic: str) -> bool:
        """Clear chat history for a specific student and topic without touching other topics."""
        data = self._load()
        if student_id in data and topic in data[student_id]:
            data[student_id][topic] = []
            self._save(data)
            return True
        return False

    def get_recent_context_for_prompt(self, student_id: str, topic: str, max_turns: int = 6) -> str:
        """Format recent dialogue turns to inject into the LLM prompt for multi-turn awareness."""
        history = self.get_history(student_id, topic)
        if not history:
            return ""

        recent = history[-max_turns:]
        lines = []
        for msg in recent:
            role_label = "Student" if msg.get("role") == "student" else "AI Tutor"
            lines.append(f"{role_label}: {msg.get('text', '')}")
        return "\n".join(lines)
