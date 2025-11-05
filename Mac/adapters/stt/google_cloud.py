"""
Google Cloud Speech-to-Text Adapter

Uses Google Cloud Speech-to-Text API for transcription.
Requires Google Cloud credentials and API key.
"""

import numpy as np
from core.stt_adapter import STTAdapter
import os


class GoogleCloudAdapter(STTAdapter):
    """Adapter for Google Cloud Speech-to-Text."""

    def __init__(self, config: dict):
        super().__init__(config)
        self.api_key = config.get('api_key', os.getenv('GOOGLE_CLOUD_API_KEY'))
        self.language_code = config.get('language_code', 'en-US')
        self.client = None

    def _init_client(self):
        """Initialize Google Cloud Speech client."""
        if self.client is None:
            try:
                from google.cloud import speech
                # If API key is provided as an environment variable
                if self.api_key:
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = self.api_key
                self.client = speech.SpeechClient()
            except ImportError:
                raise ImportError(
                    "google-cloud-speech not installed. Install with: pip install google-cloud-speech"
                )

    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio using Google Cloud Speech-to-Text.

        Args:
            audio_data: Audio samples as float32 numpy array
            sample_rate: Sample rate of the audio

        Returns:
            Transcribed text
        """
        self._init_client()

        try:
            from google.cloud import speech

            # Convert float32 to int16 for Google Cloud
            audio_int16 = (audio_data * 32767).astype(np.int16)
            audio_bytes = audio_int16.tobytes()

            audio = speech.RecognitionAudio(content=audio_bytes)
            config = speech.RecognitionConfig(
                encoding=speech.RecognitionConfig.AudioEncoding.LINEAR16,
                sample_rate_hertz=sample_rate,
                language_code=self.language_code,
                enable_automatic_punctuation=True,
            )

            response = self.client.recognize(config=config, audio=audio)

            # Combine all results
            transcripts = []
            for result in response.results:
                if result.alternatives:
                    transcripts.append(result.alternatives[0].transcript)

            if not transcripts:
                return ""

            return " ".join(transcripts).strip()

        except Exception as e:
            raise RuntimeError(f"Google Cloud Speech transcription failed: {e}")

    def is_available(self) -> bool:
        """Check if Google Cloud Speech is configured and available."""
        try:
            from google.cloud import speech
            return bool(self.api_key) or 'GOOGLE_APPLICATION_CREDENTIALS' in os.environ
        except ImportError:
            return False

    def get_name(self) -> str:
        return "Google Cloud Speech"
