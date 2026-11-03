"""Text-to-speech interface for the EduAdapt Member 4 module."""

import os
from pathlib import Path
import re
from typing import Optional

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    import win32com.client
except ImportError:
    win32com = None


def clean_text_for_speech(text: str) -> str:
    """Prepare educational text for natural speech synthesis.

    Removes markdown code fences, diagram syntax, and noisy punctuation
    so students hear clear, natural explanations rather than raw symbols.
    """
    if not text:
        return ""

    # Replace mermaid diagrams with a short summary
    cleaned = re.sub(r"```mermaid[\s\S]*?```", " [Diagram illustration shown on screen] ", text)

    # Replace C code blocks with clean audio representation
    def _code_replacer(match):
        code_body = match.group(1).strip()
        lines = [line.strip() for line in code_body.splitlines() if line.strip()]
        first_few = "; ".join(lines[:2])
        return f" [Code snippet: {first_few}. Full code displayed on screen] "

    cleaned = re.sub(r"```(?:c|C)?\s*\n([\s\S]*?)```", _code_replacer, cleaned)

    # Clean markdown headers, links, and bold/italic markup
    cleaned = re.sub(r"#{1,6}\s*", "", cleaned)
    cleaned = re.sub(r"\*\*([^*]+)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"\*([^*]+)\*", r"\1", cleaned)
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()

    return cleaned


class TextToSpeech:
    """Convert generated teaching responses into speech."""

    def __init__(self, rate: int = 170, volume: float = 1.0) -> None:
        self.rate = rate
        self.volume = volume
        self.engine = None
        self._sapi_speaker = None
        self._engine_type = None

        # 1. On Windows, prioritize native Windows SAPI SpVoice for fast, thread-safe synthesis
        if win32com is not None and os.name == "nt":
            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass
                self._sapi_speaker = win32com.client.Dispatch("SAPI.SpVoice")
                # SAPI rate range is -10 to 10; map rate ~170 to 0
                sapi_rate = max(-10, min(10, int((rate - 170) / 15)))
                self._sapi_speaker.Rate = sapi_rate
                self._sapi_speaker.Volume = int(volume * 100)
                self._engine_type = "sapi5"
            except Exception:
                self._sapi_speaker = None

        # 2. Fall back to pyttsx3 if SAPI is unavailable or on non-Windows
        if self._sapi_speaker is None and pyttsx3 is not None:
            try:
                self.engine = pyttsx3.init()
                self.engine.setProperty("rate", rate)
                self.engine.setProperty("volume", volume)
                self._engine_type = "pyttsx3"
            except Exception:
                self.engine = None

        if self.engine is None and self._sapi_speaker is None:
            raise RuntimeError(
                "Text-to-speech is unavailable. Install 'pyttsx3' or ensure Windows SAPI COM is available."
            )

    def speak(self, text: str) -> None:
        """Speak the supplied text through the system audio output."""
        if not text or not text.strip():
            raise ValueError("Text-to-speech input cannot be empty.")

        speech_text = clean_text_for_speech(text)

        if self._engine_type == "pyttsx3" and self.engine is not None:
            try:
                self.engine.say(speech_text)
                self.engine.runAndWait()
                return
            except Exception:
                # Fall back to SAPI if available
                if self._sapi_speaker is not None:
                    self._engine_type = "sapi5"

        if self._sapi_speaker is not None:
            try:
                self._sapi_speaker.Speak(speech_text)
            except Exception as e:
                # SPERR_NO_AUDIO_OUTPUT (-2147200966) happens in headless/no-speaker environments
                raise RuntimeError(
                    f"Audio playback device unavailable or uninitialized: {e}. "
                    "Use save_to_file or web audio playback in the browser."
                ) from e

    def save_to_file(self, text: str, output_path: str | Path) -> Path:
        """Save spoken text to an audio file."""
        if not text or not text.strip():
            raise ValueError("Text-to-speech input cannot be empty.")

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        speech_text = clean_text_for_speech(text)

        # Prefer Windows SAPI FileStream on NT if available for direct high-speed wav output
        if self._sapi_speaker is not None and win32com is not None:
            try:
                try:
                    import pythoncom
                    pythoncom.CoInitialize()
                except Exception:
                    pass
                stream = win32com.client.Dispatch("SAPI.SpFileStream")
                # 3 = SSFMCreateForWrite
                stream.Open(str(path), 3)
                self._sapi_speaker.AudioOutputStream = stream
                self._sapi_speaker.Speak(speech_text)
                stream.Close()
                return path
            except Exception:
                pass

        if self.engine is not None:
            self.engine.save_to_file(speech_text, str(path))
            self.engine.runAndWait()
            return path

        raise RuntimeError("Failed to generate audio file with available TTS backends.")
