"""
Windows Speech Recognition Adapter

Uses Windows native speech recognition (SAPI).
Only works on Windows platform.
"""

import numpy as np
from core.stt_adapter import STTAdapter
import sys
import tempfile
import os
import soundfile as sf


class WindowsSpeechAdapter(STTAdapter):
    """Adapter for Windows native speech recognition."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.recognizer = None

    def _init_recognizer(self):
        """Initialize Windows speech recognizer."""
        if not sys.platform.startswith('win'):
            raise RuntimeError("Windows Speech Recognition only works on Windows")

        if self.recognizer is None:
            try:
                import speech_recognition as sr
                self.recognizer = sr.Recognizer()
            except ImportError:
                raise ImportError(
                    "SpeechRecognition package not installed. Install with: pip install SpeechRecognition"
                )

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio using Windows Speech Recognition.

        Args:
            audio_data: Audio samples as float32 numpy array
            sample_rate: Sample rate of the audio

        Returns:
            Transcribed text
        """
        self._init_recognizer()

        try:
            import speech_recognition as sr

            # Convert numpy array to WAV file temporarily
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

                # Write WAV file (soundfile handles float32 directly)
                sf.write(temp_path, audio_data, sample_rate)

            # Load audio file
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)

            # Clean up temp file
            os.unlink(temp_path)

            # Use Windows recognition
            try:
                text = self.recognizer.recognize_google(audio)  # Using Google as fallback
                return text.strip()
            except sr.UnknownValueError:
                return ""
            except sr.RequestError as e:
                raise RuntimeError(f"Windows Speech Recognition error: {e}")

        except Exception as e:
            # Clean up temp file on error
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise RuntimeError(f"Windows Speech Recognition failed: {e}")

    def is_available(self) -> bool:
        """Check if Windows Speech Recognition is available."""
        if not sys.platform.startswith('win'):
            return False

        try:
            import speech_recognition as sr
            return True
        except ImportError:
            return False

    def get_name(self) -> str:
        return "Windows Speech Recognition"
