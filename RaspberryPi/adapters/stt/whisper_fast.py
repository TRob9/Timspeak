"""
Faster Whisper Adapter

Uses faster-whisper for 4x faster transcription with less memory usage.
Based on CTranslate2 implementation.
"""

import numpy as np
from core.stt_adapter import STTAdapter


class WhisperFastAdapter(STTAdapter):
    """Adapter for faster-whisper (optimized Whisper implementation)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.model = None
        self.model_size = config.get('model_size', 'base')
        self.language = config.get('language', 'en')
        self.device = config.get('device', 'cpu')
        self.compute_type = config.get('compute_type', 'int8')

    def _load_model(self):
        """Lazy-load the faster-whisper model on first use."""
        if self.model is None:
            try:
                from faster_whisper import WhisperModel
                print(f"Loading faster-whisper model: {self.model_size}")
                self.model = WhisperModel(
                    self.model_size,
                    device=self.device,
                    compute_type=self.compute_type
                )
                print("Faster-whisper model loaded successfully")
            except ImportError:
                raise ImportError(
                    "faster-whisper not installed. Install with: pip install faster-whisper"
                )
            except Exception as e:
                raise RuntimeError(f"Failed to load faster-whisper model: {e}")

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio using faster-whisper.

        Args:
            audio_data: Audio samples as float32 numpy array
            sample_rate: Sample rate of the audio

        Returns:
            Transcribed text
        """
        self._load_model()

        try:
            # faster-whisper expects float32 audio normalized to [-1, 1]
            segments, info = self.model.transcribe(
                audio_data,
                language=self.language,
                beam_size=5,
                vad_filter=True,  # Voice activity detection for better results
                vad_parameters=dict(
                    min_silence_duration_ms=500
                )
            )

            # Combine all segments into a single text
            text = " ".join([segment.text for segment in segments])

            return text.strip()

        except Exception as e:
            raise RuntimeError(f"Faster-whisper transcription failed: {e}")

    def is_available(self) -> bool:
        """Check if faster-whisper is installed."""
        try:
            from faster_whisper import WhisperModel
            return True
        except ImportError:
            return False

    def get_name(self) -> str:
        return f"Faster Whisper ({self.model_size})"

    def cleanup(self):
        """Clean up model from memory."""
        if self.model is not None:
            del self.model
            self.model = None
