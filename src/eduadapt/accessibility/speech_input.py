"""Optional Voice Input Interface (Member 4 Contribution).

Provides an optional speech-to-text hook.
Requires no background listening or continuous microphone agent.
If whisper is not installed, gracefully informs the caller with an informative message.
"""

from pathlib import Path
from typing import Optional


def transcribe_audio(audio_path: str | Path) -> str:
    """Transcribe an audio file to text using Whisper if available.

    Args:
        audio_path: Path to the target audio file (.wav, .mp3, etc.)

    Returns:
        Transcribed text string.

    Raises:
        FileNotFoundError: If the specified audio file does not exist.
        RuntimeError: If Whisper is not installed in the environment.
    """
    path = Path(audio_path)
    if not path.is_file():
        raise FileNotFoundError(f"Audio file not found at '{path}'")

    try:
        import whisper  # type: ignore
    except ImportError as e:
        raise RuntimeError(
            "Whisper speech input is optional and requires the 'openai-whisper' package. "
            "Install via 'pip install openai-whisper' to enable voice transcription."
        ) from e

    model = whisper.load_model("base")
    result = model.transcribe(str(path))
    return str(result.get("text", "")).strip()
