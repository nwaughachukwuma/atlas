"""
video_index collection — multimodal insights per video segment.

Manages the zvec collection that stores embeddings and metadata produced by
VideoProcessor, keyed by a stable video_id.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Optional

from pydantic import BaseModel

from .utils import logger
from .uuid import uuid

if TYPE_CHECKING:
    from zvec import Collection

    from .video_processor import VideoDescription, VideoProcessorResult


# ---------------------------------------------------------------------------
# zvec helpers — resolved lazily so the C-extension never loads on --help
# ---------------------------------------------------------------------------


def _open_collection(path: str) -> "Collection":
    import zvec

    return zvec.open(path=path)  # type: ignore[attr-defined]


def _create_collection(path: str, schema) -> "Collection":
    import zvec

    return zvec.create_and_open(path=path, schema=schema)


def _get_or_create(path: str, schema) -> "Collection":
    """Open existing collection or create a new one."""
    p = Path(path)
    if p.exists() and any(p.iterdir()):
        try:
            return _open_collection(path)
        except Exception:
            pass
    return _create_collection(path, schema)


def _make_schema(collection_name: str, embedding_dim: int):
    """Return the CollectionSchema for video_index."""
    from zvec import (
        CollectionSchema,
        DataType,
        FieldSchema,
        HnswIndexParam,
        InvertIndexParam,
        MetricType,
        VectorSchema,
    )

    return CollectionSchema(
        name=collection_name,
        vectors=VectorSchema(
            name="embedding",
            data_type=DataType.VECTOR_FP32,
            dimension=embedding_dim,
            index_param=HnswIndexParam(metric_type=MetricType.COSINE),
        ),
        fields=[
            FieldSchema(
                "video_id",
                DataType.STRING,
                index_param=InvertIndexParam(enable_extended_wildcard=False),
            ),
            FieldSchema("start", DataType.FLOAT),
            FieldSchema("end", DataType.FLOAT),
            FieldSchema("content", DataType.STRING),
            FieldSchema("metadata", DataType.STRING),
        ],
    )


def _make_doc(
    doc_id: str,
    embedding: list,
    video_id: str,
    start: float,
    end: float,
    content: str,
    metadata: dict,
):
    """Build a zvec Doc for video_index."""
    from zvec import Doc

    return Doc(
        id=doc_id,
        vectors={"embedding": embedding},
        fields={
            "video_id": video_id,
            "start": start,
            "end": end,
            "content": content,
            "metadata": json.dumps(metadata),
        },
    )


def _make_vector_query(embedding: list):
    """Build a zvec VectorQuery."""
    from zvec import VectorQuery

    return VectorQuery("embedding", vector=embedding)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class IndexDocument(BaseModel):
    """A single document to index in video_index."""

    id: str
    video_id: str
    start: float
    end: float
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = {}


class SearchResult(BaseModel):
    """A document returned by a video_index query."""

    id: str
    score: float
    video_id: str
    start: float
    end: float
    content: str
    metadata: dict[str, Any] = {}


class VideoEntry(BaseModel):
    """Lightweight registry entry for an indexed video."""

    video_id: str
    indexed_at: str


# ---------------------------------------------------------------------------
# VideoIndex
# ---------------------------------------------------------------------------

COLLECTION_NAME = "video_index"


class VideoIndex:
    """Manages the video_index zvec collection."""

    def __init__(self, index_path: Path, embedding_dim: int = 768):
        """Initialise the video_index collection.

        Args:
            index_path: Directory path for this collection (e.g. ~/.atlas/index/video_index).
            embedding_dim: Embedding dimension — 768 or 3072.
        """
        self.index_path = index_path
        self.embedding_dim = embedding_dim
        self._collection: Optional["Collection"] = None

    @property
    def collection(self) -> "Collection":
        """Lazily open or create the zvec collection."""
        if self._collection is None:
            self.index_path.mkdir(parents=True, exist_ok=True)
            self._collection = _get_or_create(
                str(self.index_path),
                _make_schema(COLLECTION_NAME, self.embedding_dim),
            )
        return self._collection

    def _uuid(self) -> str:
        """Generate a random 16-character document ID."""
        return uuid(16)

    def _create_searchable_content(self, description: "VideoDescription") -> str:
        """Concatenate all analysis attr values into a single searchable string."""
        parts = []
        for analysis in description.video_analysis:
            attr_name = " ".join(analysis.attr.upper().split("_"))
            parts.append(f"{attr_name}: {analysis.value}")
        return "\n".join(parts)

    async def index_video_result(
        self,
        result: "VideoProcessorResult",
        video_id: str,
        batch_size: int = 10,
    ) -> int:
        """Embed and insert all segments from a VideoProcessorResult.

        Args:
            result: Output of VideoProcessor.
            video_id: Stable identifier assigned to this video.
            batch_size: Number of docs per zvec insert call.

        Returns:
            Total number of documents inserted.
        """
        from .text_embedding import embed_text_async

        documents: list[IndexDocument] = []

        for desc in result.video_descriptions:
            # Combined segment document
            content = self._create_searchable_content(desc)
            if not content.strip():
                continue

            embedding = await embed_text_async(content, self.embedding_dim)
            documents.append(
                IndexDocument(
                    id=self._uuid(),
                    video_id=video_id,
                    start=desc.start,
                    end=desc.end,
                    content=content,
                    embedding=embedding,
                    metadata={
                        "duration": desc.end - desc.start,
                        "indexed_at": datetime.now().isoformat(),
                    },
                )
            )

            # Per-attr granular documents
            for analysis in desc.video_analysis:
                if not analysis.value.strip():
                    continue
                analysis_embedding = await embed_text_async(analysis.value, self.embedding_dim)
                documents.append(
                    IndexDocument(
                        id=self._uuid(),
                        video_id=video_id,
                        start=desc.start,
                        end=desc.end,
                        content=f"{analysis.attr}: {analysis.value}",
                        embedding=analysis_embedding,
                        metadata={
                            "attr": analysis.attr,
                            "duration": desc.end - desc.start,
                            "indexed_at": datetime.now().isoformat(),
                        },
                    )
                )

        indexed = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            zvec_docs = [_make_doc(d.id, d.embedding, d.video_id, d.start, d.end, d.content, d.metadata) for d in batch]
            self.collection.insert(zvec_docs)
            indexed += len(zvec_docs)

        logger.info(f"Indexed {indexed} documents for video_id={video_id}")
        self.collection.flush()
        self.collection.optimize()
        return indexed

    async def search(
        self,
        query: str,
        top_k: int = 10,
        video_id: Optional[str] = None,
    ) -> List[SearchResult]:
        """Semantic search over video segments.

        Args:
            query: Natural-language query.
            top_k: Maximum results to return.
            video_id: When provided, restrict results to this video.

        Returns:
            List of SearchResult ordered by relevance.
        """
        from .text_embedding import embed_text_async

        query_embedding = await embed_text_async(query, self.embedding_dim)
        try:
            vector_query = _make_vector_query(query_embedding)
            if video_id:
                results = self.collection.query(
                    vector_query,
                    topk=top_k,
                    filter=f"video_id == {video_id}",
                )
            else:
                results = self.collection.query(vector_query, topk=top_k)
        except Exception as e:
            logger.error(f"Error querying video_index: {e}")
            return []

        return [
            SearchResult(
                id=r.id,
                score=r.score or 0,
                video_id=r.field("video_id"),  # type: ignore[arg-type]
                start=r.field("start"),  # type: ignore[arg-type]
                end=r.field("end"),  # type: ignore[arg-type]
                content=r.field("content"),  # type: ignore[arg-type]
                metadata=json.loads(r.field("metadata")),  # type: ignore[arg-type]
            )
            for r in results
        ]

    def delete_by_video(self, video_id: str) -> None:
        """Delete all documents for a given video_id."""
        try:
            self.collection.delete_by_filter(filter=f"video_id == {video_id}")
        except Exception as e:
            logger.error(f"Error deleting video_index docs for video_id={video_id}: {e}")

    def delete(self, doc_id: str) -> None:
        """Delete a single document by ID."""
        try:
            self.collection.delete(ids=doc_id)
        except Exception as e:
            logger.error(f"Error deleting video_index doc {doc_id}: {e}")

    @property
    def stats(self) -> Any:
        """Raw zvec collection stats."""
        return self.collection.stats
