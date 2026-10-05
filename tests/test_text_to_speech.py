from pathlib import Path

import pytest

from src.member4.text_to_speech import TextToSpeech


class FakeEngine:
    def __init__(self):
        self.spoken_text = None
        self.saved_text = None
        self.saved_path = None

    def setProperty(self, name, value):
        pass

    def say(self, text):
        self.spoken_text = text

    def runAndWait(self):
        pass

    def save_to_file(self, text, path):
        self.saved_text = text
        self.saved_path = path


def test_text_to_speech_speaks_text(monkeypatch):
    engine = FakeEngine()

    monkeypatch.setattr(
        "src.member4.text_to_speech.pyttsx3.init",
        lambda: engine,
    )

    tts = TextToSpeech()
    tts.speak("Explain pointers in C.")

    assert engine.spoken_text == "Explain pointers in C."


def test_text_to_speech_rejects_empty_text(monkeypatch):
    engine = FakeEngine()

    monkeypatch.setattr(
        "src.member4.text_to_speech.pyttsx3.init",
        lambda: engine,
    )

    tts = TextToSpeech()

    with pytest.raises(ValueError):
        tts.speak("")


def test_text_to_speech_saves_audio(monkeypatch, tmp_path):
    engine = FakeEngine()

    monkeypatch.setattr(
        "src.member4.text_to_speech.pyttsx3.init",
        lambda: engine,
    )

    tts = TextToSpeech()

    output_file = tmp_path / "response.wav"
    result = tts.save_to_file(
        "Pointers store memory addresses.",
        output_file,
    )

    assert result == output_file
    assert engine.saved_text == "Pointers store memory addresses."
    assert engine.saved_path == str(output_file)