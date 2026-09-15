"""TF-IDF retrieval engine for operational policy documents."""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DOCS_DIR = Path(__file__).resolve().parents[1] / "documents"


class RAGRetriever:
    """Lightweight TF-IDF retrieval over a small policy document corpus."""

    def __init__(self, docs_dir: Optional[Path] = None):
        self._docs_dir = docs_dir or DOCS_DIR
        self._documents: dict[str, str] = {}
        self._vectorizer = None
        self._matrix = None
        self._doc_names: list[str] = []
        self._load()

    def _load(self) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer

        docs = {}
        for path in sorted(self._docs_dir.glob("*.md")):
            try:
                docs[path.stem] = path.read_text(encoding="utf-8")
            except Exception as e:
                logger.warning(f"Could not load {path}: {e}")

        if not docs:
            logger.warning("No RAG documents found.")
            return

        self._documents = docs
        self._doc_names = list(docs.keys())
        corpus = list(docs.values())

        self._vectorizer = TfidfVectorizer(
            stop_words="english",
            ngram_range=(1, 2),
            max_features=5000,
        )
        self._matrix = self._vectorizer.fit_transform(corpus)
        logger.info(f"RAG retriever loaded {len(docs)} documents.")

    def retrieve(self, query: str, top_k: int = 2) -> list[dict]:
        """Return the top-k most relevant document chunks for the query."""
        if self._vectorizer is None or self._matrix is None:
            return []

        import numpy as np
        from sklearn.metrics.pairwise import cosine_similarity

        q_vec = self._vectorizer.transform([query])
        scores = cosine_similarity(q_vec, self._matrix)[0]
        top_indices = np.argsort(scores)[::-1][:top_k]

        results = []
        for idx in top_indices:
            if scores[idx] > 0.01:
                name = self._doc_names[idx]
                snippet = self._extract_relevant_snippet(
                    self._documents[name], query
                )
                results.append({
                    "document": name,
                    "score": round(float(scores[idx]), 4),
                    "snippet": snippet,
                })

        return results

    def _extract_relevant_snippet(self, text: str, query: str, max_chars: int = 600) -> str:
        """Extract the most relevant paragraph from a document."""
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
        if not paragraphs:
            return text[:max_chars]

        query_words = set(query.lower().split())
        scored = []
        for para in paragraphs:
            words = set(para.lower().split())
            overlap = len(query_words & words)
            scored.append((overlap, para))

        scored.sort(key=lambda x: x[0], reverse=True)
        best = scored[0][1] if scored else paragraphs[0]
        return best[:max_chars] + ("..." if len(best) > max_chars else "")


# Singleton
_retriever: Optional[RAGRetriever] = None


def get_retriever() -> RAGRetriever:
    global _retriever
    if _retriever is None:
        _retriever = RAGRetriever()
    return _retriever
