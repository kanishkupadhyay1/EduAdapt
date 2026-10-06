"""Accessibility Package Exports."""

from eduadapt.accessibility.formatter import AccessibilityFormatter
from eduadapt.accessibility.speech_input import transcribe_audio
from eduadapt.accessibility.speech_output import speak_text

__all__ = ["AccessibilityFormatter", "transcribe_audio", "speak_text"]
