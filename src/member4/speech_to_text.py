"""Speech-to-text interface for the EduAdapt Member 4 module."""

import os
from pathlib import Path
import shutil
from typing import Optional

# Ensure local ffmpeg binaries are discovered if installed in C:\tools\ffmpeg\bin
if not shutil.which("ffmpeg"):
    ffmpeg_dir = Path(r"C:\tools\ffmpeg\bin")
    if ffmpeg_dir.is_dir():
        os.environ["PATH"] = str(ffmpeg_dir) + os.pathsep + os.environ.get("PATH", "")

try:
    import whisper
except ImportError:
    whisper = None

# Global model cache to prevent expensive model re-loading on every audio request
_WHISPER_CACHE: dict = {}


class SpeechToText:
    """Convert spoken audio into text using Whisper."""

    def __init__(self, model_name: str = "base") -> None:
        """
        Initialize the Whisper model.

        Uses cached model weights to avoid redundant disk I/O.
        """
        self.model_name = model_name
        if whisper is None:
            raise RuntimeError(
                "Whisper speech input is optional and requires 'openai-whisper'. "
                "Install via 'pip install openai-whisper'."
            )
        if model_name in _WHISPER_CACHE:
            self._model = _WHISPER_CACHE[model_name]
        else:
            try:
                self._model = whisper.load_model(model_name)
                _WHISPER_CACHE[model_name] = self._model
            except Exception as e:
                # Fall back to tiny model if base failed
                if model_name != "tiny":
                    try:
                        self._model = whisper.load_model("tiny")
                        self.model_name = "tiny"
                        _WHISPER_CACHE["tiny"] = self._model
                    except Exception:
                        raise RuntimeError(f"Failed to load Whisper model '{model_name}': {e}") from e
                else:
                    raise RuntimeError(f"Failed to load Whisper model '{model_name}': {e}") from e

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

        if path.stat().st_size == 0:
            raise ValueError(f"Audio file is empty (0 bytes): {path}")

        result = self._model.transcribe(str(path))
        text = result.get("text", "")
        return text.strip()
