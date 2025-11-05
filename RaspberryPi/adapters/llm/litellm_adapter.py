"""
LiteLLM Adapter

Uses LiteLLM to provide a unified interface for multiple LLM providers
(Claude, GPT-4, Ollama, and 100+ others).
"""

from core.llm_adapter import LLMAdapter
import os


class LiteLLMAdapter(LLMAdapter):
    """Unified adapter for multiple LLM providers via LiteLLM."""

    def __init__(self, provider_name: str, config: dict, cleaning_prompt: str):
        """
        Initialize LiteLLM adapter for a specific provider.

        Args:
            provider_name: Name of the provider (claude, openai, ollama, etc.)
            config: Configuration for this provider
            cleaning_prompt: System prompt for cleaning dictation
        """
        super().__init__(config, cleaning_prompt)
        self.provider_name = provider_name
        self.model = config.get('model')
        self.api_key = config.get('api_key', self._get_env_api_key())
        self.base_url = config.get('base_url', None)
        self.max_tokens = config.get('max_tokens', 1000)
        self.temperature = config.get('temperature', 0.3)

    def _get_env_api_key(self):
        """Get API key from environment variable based on provider."""
        env_keys = {
            'claude': 'ANTHROPIC_API_KEY',
            'openai': 'OPENAI_API_KEY',
            'ollama': None,  # Ollama doesn't need an API key
        }
        env_key = env_keys.get(self.provider_name)
        return os.getenv(env_key) if env_key else None

    def clean_text(self, raw_text: str) -> str:
        """
        Clean raw dictated text using the configured LLM provider.

        Args:
            raw_text: Original transcribed text from STT engine

        Returns:
            Cleaned and polished text
        """
        try:
            from litellm import completion

            # Prepare messages
            messages = [
                {"role": "system", "content": self.cleaning_prompt},
                {"role": "user", "content": raw_text}
            ]

            # Format model name for litellm
            # Some providers need explicit prefixes, others auto-detect
            model_name = self.model

            # Providers that need explicit prefixes
            needs_prefix = ['ollama', 'huggingface', 'azure', 'bedrock', 'vertex_ai']

            # Add prefix if needed and not already present
            if self.provider_name in needs_prefix:
                prefix = f"{self.provider_name}/"
                if not model_name.startswith(prefix):
                    model_name = f"{prefix}{model_name}"

            # Build completion kwargs
            kwargs = {
                "model": model_name,
                "messages": messages,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
            }

            # Add API key if present
            if self.api_key:
                kwargs["api_key"] = self.api_key

            # Add base URL for local providers like Ollama
            if self.base_url:
                kwargs["api_base"] = self.base_url

            # Call LiteLLM
            response = completion(**kwargs)

            # Extract cleaned text
            cleaned_text = response.choices[0].message.content.strip()

            return cleaned_text

        except Exception as e:
            raise RuntimeError(f"LLM cleaning failed for provider '{self.provider_name}': {e}")

    def is_available(self) -> bool:
        """Check if LiteLLM and the provider are configured."""
        try:
            import litellm

            # Ollama: Check if server is running
            if self.provider_name == 'ollama':
                try:
                    import requests
                    response = requests.get(f"{self.base_url}/api/tags", timeout=2)
                    return response.status_code == 200
                except:
                    return False

            # Other providers need API key
            return bool(self.api_key)

        except ImportError:
            return False

    def get_name(self) -> str:
        """Get human-readable name."""
        provider_names = {
            'claude': 'Claude (Anthropic)',
            'openai': 'OpenAI GPT',
            'ollama': 'Ollama (Local)',
        }
        return provider_names.get(self.provider_name, f"LLM ({self.provider_name})")
