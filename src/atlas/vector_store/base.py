"""
BaseCollection — shared zvec collection lifecycle and helpers.

Subclasses (VideoIndex, VideoChat) inherit:
  • Lazy collection open/create via the ``collection`` property
  • _new_id(), stats property
  • Module-level zvec factory helpers (_open_collection, _create_collection,
    _get_or_create, _make_vector_query)

Each subclass is responsible for:
  • Defining its own COLLECTION_NAME and schema via _build_schema()
  • Building collection-specific Doc objects via _make_doc()
  • Implementing its domain read/write methods
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from ..uuid import uuid

if TYPE_CHECKING:
    from zvec import Collection


# ---------------------------------------------------------------------------
# Module-level zvec factory helpers
# Resolved lazily so the C-extension never loads on --help / import time.
# ---------------------------------------------------------------------------


def _open_collection(path: str) -> "Collection":
    import zvec

    return zvec.open(path=path)  # type: ignore[attr-defined]


def _create_collection(path: str, schema) -> "Collection":
    import zvec

    return zvec.create_and_open(path=path, schema=schema)


def get_or_create_collection(path: str, schema) -> "Collection":
    """Open an existing zvec collection or create a new one at *path*."""
    p = Path(path)
    if p.exists() and any(p.iterdir()):
        try:
            return _open_collection(path)
        except Exception:
            pass
    return _create_collection(path, schema)


def make_vector_query(embedding: list):
    """Build a zvec VectorQuery over the 'embedding' vector field."""
    from zvec import VectorQuery

    return VectorQuery("embedding", vector=embedding)


def build_base_vector_schema(embedding_dim: int):
    """Return the common VectorSchema used by every collection."""
    from zvec import DataType, HnswIndexParam, MetricType, VectorSchema

    return VectorSchema(
        name="embedding",
        data_type=DataType.VECTOR_FP32,
        dimension=embedding_dim,
        index_param=HnswIndexParam(metric_type=MetricType.COSINE),
    )


# ---------------------------------------------------------------------------
# BaseCollection
# ---------------------------------------------------------------------------


class BaseCollection(ABC):
    """Abstract base for zvec-backed collection wrappers.

    Subclasses must implement ``_build_schema`` to return the
    zvec CollectionSchema appropriate for their collection.

    Args:
        index_path: Directory path for this collection.
        embedding_dim: Embedding dimension — 768 or 3072.
    """

    def __init__(self, index_path: Path, embedding_dim: int = 768) -> None:
        self.index_path = index_path
        self.embedding_dim = embedding_dim
        self._collection: Optional["Collection"] = None

    # ------------------------------------------------------------------
    # Subclass contract
    # ------------------------------------------------------------------

    @abstractmethod
    def _build_schema(self):
        """Return the zvec CollectionSchema for this collection."""

    # ------------------------------------------------------------------
    # Lazy collection lifecycle
    # ------------------------------------------------------------------

    @property
    def collection(self) -> "Collection":
        """Lazily open or create the zvec collection on first access."""
        if self._collection is None:
            self.index_path.mkdir(parents=True, exist_ok=True)
            self._collection = get_or_create_collection(
                str(self.index_path),
                self._build_schema(),
            )
        return self._collection

    # ------------------------------------------------------------------
    # Shared utilities
    # ------------------------------------------------------------------

    def _new_id(self) -> str:
        """Generate a random 16-character document ID."""
        return uuid(16)

    @property
    def stats(self) -> Any:
        """Raw zvec collection stats."""
        return self.collection.stats
