from pathlib import Path

import pytest

from src.member4.accessibility import AccessibilityPipeline
from src.member4.verification import ResponseVerifier


class FakeSpeechToText:
    def transcribe(self, audio_path):
        return "Explain pointers in C"


class FakeTextToSpeech:
    def __init__(self):
        self.spoken_text = None

    def speak(self, text):
        self.spoken_text = text


def test_accessibility_text_flow():
    stt = FakeSpeechToText()
    tts = FakeTextToSpeech()

    def generate_response(query):
        return f"Answer for: {query}"

    pipeline = AccessibilityPipeline(
        speech_to_text=stt,
        text_to_speech=tts,
        response_generator=generate_response,
        verifier=ResponseVerifier(),
    )

    result = pipeline.process_text(
        "Explain pointers in C",
        source_context="PPS curriculum material",
    )

    assert result.query == "Explain pointers in C"
    assert result.response == "Answer for: Explain pointers in C"
    assert result.verification.verified is True
    assert result.verification.grounded is True
    assert tts.spoken_text == "Answer for: Explain pointers in C"


def test_accessibility_audio_flow(tmp_path):
    stt = FakeSpeechToText()
    tts = FakeTextToSpeech()

    def generate_response(query):
        return f"Answer for: {query}"

    pipeline = AccessibilityPipeline(
        speech_to_text=stt,
        text_to_speech=tts,
        response_generator=generate_response,
    )

    audio_file = tmp_path / "question.wav"
    audio_file.write_bytes(b"fake audio")

    result = pipeline.process_audio(
        audio_file,
        source_context="PPS curriculum material",
    )

    assert result.query == "Explain pointers in C"
    assert result.verification.verified is True
    assert tts.spoken_text == "Answer for: Explain pointers in C"


def test_accessibility_rejects_empty_query():
    stt = FakeSpeechToText()
    tts = FakeTextToSpeech()

    pipeline = AccessibilityPipeline(
        speech_to_text=stt,
        text_to_speech=tts,
        response_generator=lambda query: "Some response",
    )

    with pytest.raises(ValueError):
        pipeline.process_text("")