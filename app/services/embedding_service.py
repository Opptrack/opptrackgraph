from typing import List

from openai import AsyncOpenAI

from app.config.config import app_settings
from app.core.logger import logger


class EmbeddingService:
    def __init__(
        self,
        base_url: str | None = app_settings.EMBEDDING_API_BASE_URL,
        api_key: str | None = app_settings.EMBEDDING_API_KEY,
        model_name: str | None = app_settings.EMBEDDING_MODEL_NAME,
    ):
        if not api_key:
            raise ValueError("EMBEDDING_API_KEY is required")
        if not model_name:
            raise ValueError("EMBEDDING_MODEL_NAME is required")

        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name

    def _client(self) -> AsyncOpenAI:
        return AsyncOpenAI(base_url=self.base_url, api_key=self.api_key)

    async def embed_texts(self, texts: List[str]) -> List[List[float]]:
        if not texts:
            return []

        logger.info(f"Creating embeddings for {len(texts)} texts")
        client = self._client()
        resp = await client.embeddings.create(model=self.model_name, input=texts)
        vectors: List[List[float]] = [
            d.embedding
            for d in resp.data  # type: ignore[attr-defined]
        ]
        return vectors
