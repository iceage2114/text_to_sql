"""
Centralised LLM and embedding configuration for GitHub Models API.

GitHub Models uses the OpenAI-compatible API at:
  https://models.inference.ai.azure.com

Both ChatOpenAI (agents) and OpenAIEmbeddings (ChromaDB) are wired to this
endpoint using the GITHUB_TOKEN from .env.
"""
from __future__ import annotations

from typing import Any, Dict, List

from chromadb import EmbeddingFunction, Documents
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from config import settings


def get_chat_llm(temperature: float = 0) -> ChatOpenAI:
    """Return a ChatOpenAI instance pointed at the GitHub Models endpoint."""
    return ChatOpenAI(
        model=settings.chat_model,
        api_key=settings.openai_key,
        base_url=settings.openai_base_url,
        temperature=temperature,
    )


class GitHubEmbeddingFunction(EmbeddingFunction[Documents]):
    """
    ChromaDB 1.5.x-compatible embedding function backed by GitHub Models.

    Implements the full EmbeddingFunction protocol:
      - __call__         : embed documents
      - name()           : unique identifier stored in collection config
      - get_config()     : serialisable config for persistence
      - build_from_config: reconstruct from stored config
    """

    def __init__(self) -> None:
        self._embedder = OpenAIEmbeddings(
            model=settings.embedding_model,
            api_key=settings.openai_key,
            base_url=settings.openai_base_url,
        )

    def __call__(self, input: Documents) -> List[List[float]]:  # noqa: A002
        return self._embedder.embed_documents(input)

    @staticmethod
    def name() -> str:
        return "github-openai-embeddings"

    def get_config(self) -> Dict[str, Any]:
        return {
            "model": settings.embedding_model,
            "base_url": settings.openai_base_url,
        }

    @staticmethod
    def build_from_config(config: Dict[str, Any]) -> "GitHubEmbeddingFunction":
        return GitHubEmbeddingFunction()
