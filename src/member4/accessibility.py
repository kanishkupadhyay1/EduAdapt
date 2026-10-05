"""Accessibility input/output flow for the EduAdapt Member 4 module."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from .speech_to_text import SpeechToText
from .text_to_speech import TextToSpeech
from .verification import ResponseVerifier, VerificationResult


@dataclass
class AccessibilityResult:
    """Result returned by the accessibility pipeline."""

    query: str
    response: str
    verification: VerificationResult


class AccessibilityPipeline:
    """
    Connect speech input, response verification, and speech output.

    The response generator is injected so Member 1's Mistral
    implementation can be connected later without changing this module.
    """

    def __init__(
        self,
        speech_to_text: SpeechToText,
        text_to_speech: TextToSpeech,
        response_generator: Callable[[str], str],
        verifier: Optional[ResponseVerifier] = None,
    ) -> None:
        self.speech_to_text = speech_to_text
        self.text_to_speech = text_to_speech
        self.response_generator = response_generator
        self.verifier = verifier or ResponseVerifier()

    def process_text(
        self,
        query: str,
        source_context: Optional[str] = None,
        speak_response: bool = True,
    ) -> AccessibilityResult:
        """Process a text query through generation, verification, and TTS."""

        if not query or not query.strip():
            raise ValueError("Accessibility query cannot be empty.")

        response = self.response_generator(query)

        verification = self.verifier.verify(
            generated_response=response,
            source_context=source_context,
        )

        if verification.verified and speak_response:
            self.text_to_speech.speak(response)

        return AccessibilityResult(
            query=query,
            response=response,
            verification=verification,
        )

    def process_audio(
        self,
        audio_path: str | Path,
        source_context: Optional[str] = None,
        speak_response: bool = True,
    ) -> AccessibilityResult:
        """Transcribe audio and process the resulting text query."""

        query = self.speech_to_text.transcribe(audio_path)

        return self.process_text(
            query=query,
            source_context=source_context,
            speak_response=speak_response,
        )