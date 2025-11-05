"""
OpenAI Whisper Local Adapter

Uses the official openai-whisper package for local transcription.
Slower than faster-whisper but the original implementation.
"""

import numpy as np
from core.stt_adapter import STTAdapter
import os


class WhisperLocalAdapter(STTAdapter):
    """Adapter for official OpenAI Whisper (local)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.model = None
        self.model_size = config.get('model_size', 'base')
        self.language = config.get('language', 'en')

    def _load_model(self):
        """Lazy-load the Whisper model on first use."""
        if self.model is None:
            try:
                import whisper
                print(f"Loading Whisper model: {self.model_size}")
                self.model = whisper.load_model(self.model_size)
                print("Whisper model loaded successfully")
            except ImportError:
                raise ImportError(
                    "openai-whisper not installed. Install with: pip install openai-whisper"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load Whisper model: {e}")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio using OpenAI Whisper.

        Args:
            audio_data: Audio samples as float32 numpy array
            sample_rate: Sample rate of the audio

        Returns:
            Transcribed text
        """
        self._load_model()

        try:
            # Whisper expects float32 audio normalized to [-1, 1]
            # and will handle resampling internally to 16kHz if needed
            result = self.model.transcribe(
                audio_data,
                language=self.language,
                fp16=False  # Use FP32 for CPU compatibility
            )

            return result['text'].strip()

        except Exception as e:
            raise RuntimeError(f"Whisper transcription failed: {e}")

    def is_available(self) -> bool:
        """Check if openai-whisper is installed."""
        try:
            import whisper
            return True
        except ImportError:
            return False

    def get_name(self) -> str:
        return f"Whisper Local ({self.model_size})"

    def cleanup(self):
        """Clean up model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
