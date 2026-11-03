"""Test suite for EduAdapt Audio Endpoints (STT & TTS) and Member 4 integration."""

from pathlib import Path
import pytest

from eduadapt.api import (
    AudioSynthesizeRequest,
    get_audio_status,
    synthesize_speech,
)
from member4.speech_to_text import SpeechToText
from member4.text_to_speech import clean_text_for_speech


def test_audio_status_endpoint():
    """Verify that get_audio_status returns pipeline readiness."""
    data = get_audio_status()
    assert "speech_to_text_available" in data
    assert "text_to_speech_available" in data
    assert data["speech_to_text_available"] is True
    assert data["text_to_speech_available"] is True


def test_clean_text_for_speech():
    """Verify that code blocks, markdown headings, and diagrams are cleaned for speech."""
    raw = (
        "# Unit 4: Pointers\n"
        "Pointers hold **memory addresses**.\n"
        "```mermaid\ngraph TD\nA-->B\n```\n"
        "Here is an example:\n"
        "```c\nint *p = &x;\n*p = 10;\n```\n"
        "Understanding this is key."
    )
    cleaned = clean_text_for_speech(raw)
    assert "#" not in cleaned
    assert "```mermaid" not in cleaned
    assert "Diagram illustration shown on screen" in cleaned
    assert "Code snippet" in cleaned
    assert "Pointers hold memory addresses" in cleaned


def test_synthesize_endpoint_direct():
    """Verify direct audio synthesis produces valid WAV bytes."""
    req = AudioSynthesizeRequest(text="Pointer variables in C store addresses of data.", rate=170)
    response = synthesize_speech(req)
    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/wav"
    assert len(response.body) > 1000


def test_synthesize_rejects_empty():
    """Verify that empty text produces error."""
    req = AudioSynthesizeRequest(text="", rate=170)
    with pytest.raises(Exception):
        synthesize_speech(req)


def test_speech_to_text_rejects_missing_and_empty(tmp_path):
    """Verify STT raises appropriate errors on missing or empty files."""
    stt = SpeechToText(model_name="tiny")

    with pytest.raises(FileNotFoundError):
        stt.transcribe(tmp_path / "non_existent.wav")

    empty_file = tmp_path / "empty.wav"
    empty_file.write_bytes(b"")
    with pytest.raises(ValueError):
        stt.transcribe(empty_file)
