"""Text-to-speech interface for the EduAdapt Member 4 module."""

from pathlib import Path
from typing import Optional

import pyttsx3


class TextToSpeech:
    """Convert generated teaching responses into speech."""

    def __init__(self, rate: int = 170, volume: float = 1.0) -> None:
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", rate)
        self.engine.setProperty("volume", volume)

    def speak(self, text: str) -> None:
        """Speak the supplied text through the system audio output."""
        if not text or not text.strip():
            raise ValueError("Text-to-speech input cannot be empty.")

        self.engine.say(text)
        self.engine.runAndWait()

    def save_to_file(self, text: str, output_path: str | Path) -> Path:
        """Save spoken text to an audio file."""
        if not text or not text.strip():
            raise ValueError("Text-to-speech input cannot be empty.")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        self.engine.save_to_file(text, str(path))
        self.engine.runAndWait()

        return path