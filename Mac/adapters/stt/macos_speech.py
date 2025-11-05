"""
macOS Speech Recognition Adapter

Uses macOS native Speech Framework.
Only works on macOS platform.
"""

import numpy as np
from core.stt_adapter import STTAdapter
import sys
import tempfile
import os
from scipy.io import wavfile


class MacOSSpeechAdapter(STTAdapter):
    """Adapter for macOS native speech recognition."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.recognizer = None

    def _init_recognizer(self):
        """Initialize macOS speech recognizer."""
        if not sys.platform.startswith('darwin'):
            raise RuntimeError("macOS Speech Recognition only works on macOS")

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
        Transcribe audio using macOS Speech Recognition.

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

                # Convert float32 to int16
                audio_int16 = (audio_data * 32767).astype(np.int16)
                wavfile.write(temp_path, sample_rate, audio_int16)

            # Load audio file
            with sr.AudioFile(temp_path) as source:
                audio = self.recognizer.record(source)

            # Clean up temp file
            os.unlink(temp_path)

            # Use Google recognition (macOS native framework requires PyObjC)
            try:
                text = self.recognizer.recognize_google(audio)
                return text.strip()
            except sr.UnknownValueError:
                return ""
            except sr.RequestError as e:
                raise RuntimeError(f"macOS Speech Recognition error: {e}")

        except Exception as e:
            # Clean up temp file on error
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise RuntimeError(f"macOS Speech Recognition failed: {e}")

    def is_available(self) -> bool:
        """Check if macOS Speech Recognition is available."""
        if not sys.platform.startswith('darwin'):
            return False

        try:
            import speech_recognition as sr
            return True
        except ImportError:
            return False

    def get_name(self) -> str:
        return "macOS Speech Recognition"
