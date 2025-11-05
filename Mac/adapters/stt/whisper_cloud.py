"""
OpenAI Whisper Cloud Adapter

Uses OpenAI's hosted Whisper API for transcription.
Requires an OpenAI API key.
"""

import numpy as np
from core.stt_adapter import STTAdapter
import io
import os
import soundfile as sf
import tempfile


class WhisperCloudAdapter(STTAdapter):
    """Adapter for OpenAI Whisper API (cloud-based)."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get('api_key', os.getenv('OPENAI_API_KEY'))
        self.model = config.get('model', 'whisper-1')
        self.client = None

    def _init_client(self):
        """Initialize OpenAI client."""
        if self.client is None:
            try:
                from openai import OpenAI
                if not self.api_key:
                    raise ValueError("OpenAI API key not configured")
                self.client = OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package not installed. Install with: pip install openai"
                )

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio using OpenAI Whisper API.

        Args:
            audio_data: Audio samples as float32 numpy array
            sample_rate: Sample rate of the audio

        Returns:
            Transcribed text
        """
        self._init_client()

        try:
            # Convert numpy array to WAV file in memory
            # OpenAI API requires a file-like object
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_path = temp_file.name

                # Write WAV file (soundfile handles float32 directly)
                sf.write(temp_path, audio_data, sample_rate)

            # Send to OpenAI API
            with open(temp_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model=self.model,
                    file=audio_file,
                    response_format="text"
                )

            # Clean up temp file
            os.unlink(temp_path)

            return response.strip()

        except Exception as e:
            # Clean up temp file on error
            if 'temp_path' in locals():
                try:
                    os.unlink(temp_path)
                except:
                    pass
            raise RuntimeError(f"OpenAI Whisper API transcription failed: {e}")

    def is_available(self) -> bool:
        """Check if OpenAI API is configured and available."""
        try:
            from openai import OpenAI
            return bool(self.api_key)
        except ImportError:
            return False

    def get_name(self) -> str:
        return "Whisper Cloud (OpenAI API)"
