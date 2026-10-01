from app.config import settings
from app.ai.base import BaseAIProvider
from app.ai.mock_provider import MockAIProvider
from app.ai.gemini_provider import GeminiProvider

def get_ai_provider() -> BaseAIProvider:
    if settings.AI_PROVIDER.lower() == "gemini" and settings.GEMINI_API_KEY:
        return GeminiProvider(api_key=settings.GEMINI_API_KEY, model=settings.GEMINI_MODEL)
    return MockAIProvider()

__all__ = ["BaseAIProvider", "MockAIProvider", "GeminiProvider", "get_ai_provider"]
