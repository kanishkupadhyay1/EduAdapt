"""Speech-to-text interface for the EduAdapt Member 4 module."""

from pathlib import Path
from typing import Optional

import whisper


class SpeechToText:
    """Convert spoken audio into text using Whisper."""

    def __init__(self, model_name: str = "base") -> None:
        """
        Initialize the Whisper model.

        The base model provides a reasonable balance between
        transcription quality and local resource usage.
        """
        self.model_name = model_name
        self._model = whisper.load_model(model_name)

    def transcribe(self, audio_path: str | Path) -> str:
        """
        Transcribe an audio file and return the recognized text.

        Parameters
        ----------
        audio_path:
            Path to an audio file supported by Whisper.

        Returns
        -------
        str
            Transcribed text.
        """
        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(f"Audio file not found: {path}")

        result = self._model.transcribe(str(path))
        return result["text"].strip()