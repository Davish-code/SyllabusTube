"""ChromaDB and local vector store interface."""

from __future__ import annotations

from typing import Any


class VectorStore:
    """Wrapper for dense embedding vector storage and similarity lookup."""

    def __init__(self, collection_name: str = "syllabustube_chunks") -> None:
        self.collection_name = collection_name

    def add(
        self, ids: list[str], embeddings: list[list[float]], metadatas: list[dict[str, Any]]
    ) -> None:
        """Insert vectors and metadata into the collection."""
        raise NotImplementedError("Vector store indexing will be implemented in Phase 4.")

    def query(self, query_embedding: list[float], top_k: int = 10) -> list[dict[str, Any]]:
        """Query top-k nearest neighbors."""
        raise NotImplementedError("Vector store similarity search will be implemented in Phase 4.")
