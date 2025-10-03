from typing import List, Optional
import asyncio
from abc import ABC, abstractmethod
import openai
from app.core.config import settings


class EmbeddingProvider(ABC):
    @abstractmethod
    async def get_embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        pass


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self, api_key: str, model: str = "text-embedding-ada-002"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self.model = model

    async def get_embedding(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    async def get_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embeddings.create(
            model=self.model,
            input=texts
        )
        return [data.embedding for data in response.data]


class EmbeddingService:
    def __init__(self, provider: Optional[EmbeddingProvider] = None):
        if provider is None:
            # Default to OpenAI if API key is available
            if settings.OPENAI_API_KEY:
                provider = OpenAIEmbeddingProvider(
                    api_key=settings.OPENAI_API_KEY,
                    model=settings.EMBEDDING_MODEL
                )
            else:
                raise ValueError("No embedding provider configured. Please set OPENAI_API_KEY.")

        self.provider = provider

    async def get_embedding(self, text: str) -> List[float]:
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        # Clean and truncate text if necessary
        cleaned_text = self._clean_text(text)
        return await self.provider.get_embedding(cleaned_text)

    async def get_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        if not texts:
            return []

        # Clean texts
        cleaned_texts = [self._clean_text(text) for text in texts if text and text.strip()]

        if not cleaned_texts:
            return []

        # Process in batches to avoid API limits
        embeddings = []
        for i in range(0, len(cleaned_texts), batch_size):
            batch = cleaned_texts[i:i + batch_size]
            batch_embeddings = await self.provider.get_embeddings_batch(batch)
            embeddings.extend(batch_embeddings)

            # Add small delay between batches to respect rate limits
            if i + batch_size < len(cleaned_texts):
                await asyncio.sleep(0.1)

        return embeddings

    def _clean_text(self, text: str) -> str:
        # Remove excessive whitespace and normalize
        cleaned = " ".join(text.split())

        # Truncate if too long (OpenAI has token limits)
        max_chars = 8000  # Conservative limit for token count
        if len(cleaned) > max_chars:
            cleaned = cleaned[:max_chars] + "..."

        return cleaned