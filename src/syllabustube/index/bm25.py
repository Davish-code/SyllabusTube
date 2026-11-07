"""BM25 sparse keyword search index."""

from __future__ import annotations

from typing import Any


class BM25Index:
    """Sparse keyword index for lexical retrieval."""

    def __init__(self) -> None:
        self.corpus: list[str] = []

    def index(self, documents: list[str], metadatas: list[dict[str, Any]]) -> None:
        """Tokenize and index documents into BM25."""
        raise NotImplementedError("BM25 index construction will be implemented in Phase 4.")

    def search(self, query: str, top_k: int = 10) -> list[dict[str, Any]]:
        """Search top-k matching documents using BM25."""
        raise NotImplementedError("BM25 keyword search will be implemented in Phase 4.")
