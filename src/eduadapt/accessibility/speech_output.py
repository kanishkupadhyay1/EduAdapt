"""Optional Voice Output Interface (Member 4 Contribution).

Provides lightweight text-to-speech functionality.
Uses Windows built-in System.Speech.Synthesis or pyttsx3 when available.
Operates as a simple one-shot function; no continuous conversation agent.
"""

from pathlib import Path
import subprocess
import sys
from typing import Optional


def speak_text(text: str, output_path: Optional[str | Path] = None) -> bool:
    """Convert text to speech or save speech audio.

    Args:
        text: Text to speak.
        output_path: Optional path to save WAV audio output.

    Returns:
        True if synthesis succeeded, False otherwise.
    """
    if not text or not text.strip():
        return False

    # Shorten long text for speech if needed (e.g. summarize first 500 chars)
    spoken_summary = text.strip()
    if len(spoken_summary) > 600:
        spoken_summary = spoken_summary[:600] + "... End of preview."

    # On Windows, try System.Speech.Synthesis via PowerShell without heavy dependencies
    if sys.platform == "win32":
        try:
            # Escape double quotes and backticks for PowerShell string
            escaped_text = spoken_summary.replace("`", "``").replace('"', '`"').replace("\n", " ")
            if output_path:
                wav_path = str(Path(output_path).resolve())
                ps_script = (
                    "Add-Type -AssemblyName System.Speech; "
                    f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.SetOutputToWaveFile('{wav_path}'); "
                    f"$s.Speak('{escaped_text}'); "
                    f"$s.Dispose();"
                )
            else:
                ps_script = (
                    "Add-Type -AssemblyName System.Speech; "
                    f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                    f"$s.Speak('{escaped_text}'); "
                    f"$s.Dispose();"
                )

            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                capture_output=True,
                text=True,
                timeout=15.0,
                check=False,
            )
            return res.returncode == 0
        except Exception:
            pass

    # Fallback to pyttsx3 if installed
    try:
        import pyttsx3  # type: ignore
        engine = pyttsx3.init()
        if output_path:
            engine.save_to_file(spoken_summary, str(output_path))
        else:
            engine.say(spoken_summary)
        engine.runAndWait()
        return True
    except ImportError:
        pass

    return False
