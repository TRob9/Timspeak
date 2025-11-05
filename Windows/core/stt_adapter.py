"""
Speech-to-Text Adapter Base Class

Defines the interface that all STT adapters must implement.
"""

from abc import ABC, abstractmethod
from typing import Optional
import numpy as np


class STTAdapter(ABC):
    """Base class for all speech-to-text adapters."""

    def __init__(self, config: dict):
        """
        Initialize the STT adapter.

        Args:
            config: Configuration dictionary for this specific adapter
        """
        self.config = config
        self.enabled = config.get('enabled', True)

    @abstractmethod
    def transcribe(self, audio_data: np.ndarray, sample_rate: int) -> str:
        """
        Transcribe audio data to text.

        Args:
            audio_data: NumPy array of audio samples (float32, normalized to [-1, 1])
            sample_rate: Sample rate of the audio (e.g., 16000)

        Returns:
            Transcribed text as a string

        Raises:
            Exception: If transcription fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this STT engine is available and properly configured.

        Returns:
            True if the engine is ready to use, False otherwise
        """
        pass

    def get_name(self) -> str:
        """
        Get a human-readable name for this adapter.

        Returns:
            Display name for the adapter
        """
        return self.__class__.__name__

    def cleanup(self):
        """
        Clean up resources (override if needed).
        Called when the adapter is no longer needed.
        """
        pass
