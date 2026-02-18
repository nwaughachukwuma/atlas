"""
Vector store using zvec for local vector search
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
# Helpers — zvec symbols resolved lazily so the heavy C-extension is only
# imported when an actual index operation (not --help / --version) runs.
# ---------------------------------------------------------------------------


def _open_collection(path: str) -> "Collection":
    import zvec

    return zvec.open(path=path)  # type: ignore[attr-defined]


def _create_collection(path: str, schema) -> "Collection":
    import zvec

    return zvec.create_and_open(path=path, schema=schema)


def _make_schema(collection_name: str, embedding_dim: int):
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
                "video_path",
                DataType.STRING,
                index_param=InvertIndexParam(enable_extended_wildcard=False),
            ),
            FieldSchema("start", DataType.FLOAT),
            FieldSchema("end", DataType.FLOAT),
            FieldSchema("content", DataType.STRING),
            FieldSchema("metadata", DataType.STRING),
        ],
    )


def _make_doc(doc_id: str, embedding: list, video_path: str, start: float, end: float, content: str, metadata: dict):
    from zvec import Doc

    return Doc(
        id=doc_id,
        vectors={"embedding": embedding},
        fields={
            "video_path": video_path,
            "start": start,
            "end": end,
            "content": content,
            "metadata": json.dumps(metadata),
        },
    )


def _make_vector_query(embedding: list):
    from zvec import VectorQuery

    return VectorQuery("embedding", vector=embedding)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class IndexDocument(BaseModel):
    """Document to index in vector store"""

    id: str
    video_path: str
    start: float
    end: float
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = {}


class SearchResult(BaseModel):
    """Search result from vector store"""

    id: str
    score: float
    video_path: str
    start: float
    end: float
    content: str
    metadata: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# VectorStore
# ---------------------------------------------------------------------------


class VectorStore:
    """Local vector store using zvec"""

    DEFAULT_EMBEDDING_DIM = 768
    COLLECTION_NAME = "atlas_video_index"

    def __init__(self, store_path: Optional[str] = None, embedding_dim: int = DEFAULT_EMBEDDING_DIM):
        """Initialize zvec vector store
        Args:
            store_path: Path to store the vector index. Defaults to ~/.atlas/index
            embedding_dim: Dimension of embeddings (768 or 3072 for Gemini)
        """
        self.store_path = Path(store_path or Path.home() / ".atlas" / "index")
        self.embedding_dim = embedding_dim
        self._collection: Optional["Collection"] = None

    @property
    def collection(self) -> "Collection":
        """Get or create the zvec collection"""
        if self._collection is None:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            self._collection = self.get_collection()
        return self._collection

    def get_collection(self) -> "Collection":
        """Create or open zvec collection"""
        if self.store_path.exists():
            try:
                return _open_collection(str(self.store_path))
            except Exception:
                pass

        schema = _make_schema(self.COLLECTION_NAME, self.embedding_dim)
        return _create_collection(str(self.store_path), schema)

    def _doc_id(self) -> str:
        """Create a unique document ID"""
        return uuid(16)

    def _create_searchable_content(self, description: "VideoDescription") -> str:
        """Create searchable content from video description"""
        parts = []
        for analysis in description.video_analysis:
            attr_name = " ".join(analysis.attr.upper().split("_"))
            parts.append(f"{attr_name}: {analysis.value}")
        return "\n".join(parts)

    async def index_video_result(
        self,
        result: "VideoProcessorResult",
        batch_size=10,
    ) -> int:
        """Index video processor result
        Args:
            result: VideoProcessorResult from video processing
            batch_size: Number of documents to index at once
        Returns:
            Number of documents indexed
        """
        from .text_embedding import embed_text_async

        documents: list[IndexDocument] = []
        video_path = result.video_path
        for desc in result.video_descriptions:
            # Create a combined document for the entire segment
            content = self._create_searchable_content(desc)
            if not content.strip():
                continue

            embedding = await embed_text_async(content, self.embedding_dim)

            doc_id = self._doc_id()
            doc = IndexDocument(
                id=doc_id,
                video_path=video_path,
                start=desc.start,
                end=desc.end,
                content=content,
                embedding=embedding,
                metadata={
                    "duration": desc.end - desc.start,
                    "indexed_at": datetime.now().isoformat(),
                },
            )
            documents.append(doc)
            # Also create individual documents for each analysis type
            for analysis in desc.video_analysis:
                if not analysis.value.strip():
                    continue

                analysis_embedding = await embed_text_async(analysis.value, self.embedding_dim)
                analysis_doc = IndexDocument(
                    id=self._doc_id(),
                    video_path=video_path,
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
                documents.append(analysis_doc)

        # Insert documents in batches
        indexed = 0
        for i in range(0, len(documents), batch_size):
            batch = documents[i : i + batch_size]
            zvec_docs = [
                _make_doc(
                    doc.id,
                    doc.embedding,
                    doc.video_path,
                    doc.start,
                    doc.end,
                    doc.content,
                    doc.metadata,
                )
                for doc in batch
            ]
            self.collection.insert(zvec_docs)
            indexed += len(zvec_docs)

        logger.info(f"Indexed {indexed} documents for {video_path}")

        self.collection.flush()
        self.collection.optimize()
        return indexed

    async def search(
        self,
        query: str,
        top_k: int = 10,
        video_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """Search for similar content
        Args:
            query: Query text
            top_k: Number of results to return
            video_filter: Optional video path to filter results
        Returns:
            List of search results
        """
        from .text_embedding import embed_text_async

        query_embedding = await embed_text_async(query, self.embedding_dim)
        try:
            vector_query = _make_vector_query(query_embedding)
            if video_filter:
                results = self.collection.query(vector_query, topk=top_k, filter=f"video_path == {video_filter}")
            else:
                results = self.collection.query(vector_query, topk=top_k)
        except Exception as e:
            logger.error(f"Error querying collection: {e}")
            return []

        # Convert results
        return [
            SearchResult(
                id=result.id,
                score=result.score or 0,
                video_path=result.field("video_path"),  # type: ignore
                start=result.field("start"),  # type: ignore
                end=result.field("end"),  # type: ignore
                content=result.field("content"),  # type: ignore
                metadata=json.loads(result.field("metadata")),  # type: ignore
            )
            for result in results
        ]

    def delete_by_video(self, video_path: str):
        """Delete all documents for a video
        Args:
            video_path: Path of video to delete documents for
        """
        try:
            self.collection.delete_by_filter(filter=f"video_path == {video_path}")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")

    def delete(self, id: str):
        """Delete all documents for a video
        Args:
            id: vector id
        """
        try:
            self.collection.delete(ids=id)
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")

    def get_stats(self) -> dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "store_path": str(self.store_path),
            "embedding_dim": self.embedding_dim,
            "collection_name": self.COLLECTION_NAME,
            "col_stats": self.collection.stats,
        }


# ---------------------------------------------------------------------------
# Convenience functions
# ---------------------------------------------------------------------------


async def index_video(
    video_path: str,
    chunk_duration: int = 10,
    overlap: int = 0,
    store_path: Optional[str] = None,
) -> tuple[int, "VideoProcessorResult"]:
    """Process and index a video
    Args:
        video_path: Path to the video file
        chunk_duration: Duration of each chunk in seconds
        overlap: Overlap between chunks in seconds
        store_path: Path to store the vector index
    Returns:
        Tuple of (number of documents indexed, processing result)
    """
    from .video_processor import VideoProcessor, VideoProcessorConfig

    config = VideoProcessorConfig(
        video_path=video_path,
        chunk_duration=chunk_duration,
        overlap=overlap,
    )

    async with VideoProcessor(config) as processor:
        result = await processor.process()

    store = VectorStore(store_path=store_path)
    indexed = await store.index_video_result(result)
    return indexed, result


async def search_video(
    query: str,
    top_k: int = 10,
    video_filter: Optional[str] = None,
    store_path: Optional[str] = None,
) -> List[SearchResult]:
    """Search indexed videos
    Args:
        query: Query text
        top_k: Number of results to return
        video_filter: Optional video path to filter results
        store_path: Path to the vector index
    Returns:
        List of search results
    """
    store = VectorStore(store_path=store_path)
    return await store.search(query, top_k=top_k, video_filter=video_filter)
