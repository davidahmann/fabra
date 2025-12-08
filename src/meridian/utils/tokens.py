from abc import ABC, abstractmethod
from typing import Optional, Any
import structlog
import functools

logger = structlog.get_logger()


class TokenCounter(ABC):
    @abstractmethod
    def count(self, text: str) -> int:
        """Count tokens in text."""
        pass


class OpenAITokenCounter(TokenCounter):
    def __init__(self, model: str = "gpt-4o"):
        self.model = model
        self.encoder: Optional[Any] = None
        try:
            import tiktoken

            self.encoder = tiktoken.encoding_for_model(model)
        except Exception as e:
            logger.warning(f"Failed to load tiktoken for {model}: {e}")
            self.encoder = None

    def count(self, text: str) -> int:
        if not self.encoder:
            # Fallback estimation: chars / 4
            return len(text) // 4
        try:
            return len(self.encoder.encode(text))
        except Exception as e:
            logger.error(f"Token count error: {e}")
            return len(text) // 4


class AnthropicTokenCounter(TokenCounter):
    def __init__(self, model: str = "claude-3-5-sonnet-20240620"):
        self.model = model
        self.client = None
        try:
            from anthropic import Anthropic

            self.client = Anthropic()
        except Exception as e:
            logger.warning(f"Failed to load anthropic SDK: {e}")

    def count(self, text: str) -> int:
        if not self.client:
            return len(text) // 4

        return _get_anthropic_token_count(self.model, text)


@functools.lru_cache(maxsize=1024)
def _get_anthropic_token_count(model: str, text: str) -> int:
    try:
        # We instantiate client here (stateless mostly) to avoid passing 'self'
        from anthropic import Anthropic

        client = Anthropic()
        response = client.beta.messages.count_tokens(
            model=model, messages=[{"role": "user", "content": text}]
        )
        return response.input_tokens
    except Exception as e:
        logger.error(f"Anthropic token count error: {e}")
        return len(text) // 4
