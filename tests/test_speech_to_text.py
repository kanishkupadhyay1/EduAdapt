from pathlib import Path

import pytest

from src.member4.speech_to_text import SpeechToText


class FakeWhisperModel:
    def transcribe(self, audio_path: str):
        return {"text": "Explain pointers in C"}


def test_speech_to_text_transcribes_audio(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.member4.speech_to_text.whisper.load_model",
        lambda model_name: FakeWhisperModel(),
    )

    audio_file = tmp_path / "sample.wav"
    audio_file.write_bytes(b"fake audio data")

    stt = SpeechToText(model_name="base")
    text = stt.transcribe(audio_file)

    assert text == "Explain pointers in C"


def test_speech_to_text_rejects_missing_audio(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "src.member4.speech_to_text.whisper.load_model",
        lambda model_name: FakeWhisperModel(),
    )

    stt = SpeechToText(model_name="base")

    missing_file = tmp_path / "missing.wav"

    with pytest.raises(FileNotFoundError):
        stt.transcribe(missing_file)