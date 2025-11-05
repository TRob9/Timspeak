"""
LLM Adapter Base Class

Defines the interface for LLM adapters used for cleaning dictation.
"""

from abc import ABC, abstractmethod
from typing import Optional


class LLMAdapter(ABC):
    """Base class for all LLM adapters."""

    def __init__(self, config: dict, cleaning_prompt: str):
        """
        Initialize the LLM adapter.

        Args:
            config: Configuration dictionary for this specific adapter
            cleaning_prompt: System prompt for cleaning dictation
        """
        self.config = config
        self.cleaning_prompt = cleaning_prompt

    @abstractmethod
    def clean_text(self, raw_text: str) -> str:
        """
        Clean raw dictated text using the LLM.

        Args:
            raw_text: Original transcribed text from STT engine

        Returns:
            Cleaned and polished text

        Raises:
            Exception: If cleaning fails
        """
        pass

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if this LLM provider is available and properly configured.

        Returns:
            True if the provider is ready to use, False otherwise
        """
        pass

    def get_name(self) -> str:
        """
        Get a human-readable name for this adapter.

        Returns:
            Display name for the adapter
        """
        return self.__class__.__name__
