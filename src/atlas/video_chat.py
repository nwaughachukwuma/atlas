"""
video_chat collection — chat history (role=user|assistant) per video.

Each chat turn (question + answer) is embedded and stored here so the chat
workflow can do semantic retrieval over prior conversation context, in addition
to the sequential JSONL sidecar used for ordered history.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Any, List, Literal, Optional

from pydantic import BaseModel

from .utils import logger
from .uuid import uuid

if TYPE_CHECKING:
    from zvec import Collection


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
    """Return the CollectionSchema for video_chat."""
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
            # role supports filtering: role == "user" | "assistant"
            FieldSchema(
                "role",
                DataType.STRING,
                index_param=InvertIndexParam(enable_extended_wildcard=False),
            ),
            FieldSchema("content", DataType.STRING),
            FieldSchema("metadata", DataType.STRING),
        ],
    )


def _make_doc(
    doc_id: str,
    embedding: list,
    video_id: str,
    role: str,
    content: str,
    metadata: dict,
):
    """Build a zvec Doc for video_chat."""
    from zvec import Doc

    return Doc(
        id=doc_id,
        vectors={"embedding": embedding},
        fields={
            "video_id": video_id,
            "role": role,
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

ChatRole = Literal["user", "assistant"]


class ChatDocument(BaseModel):
    """A single chat message to index in video_chat."""

    id: str
    video_id: str
    role: ChatRole
    content: str
    embedding: list[float]
    metadata: dict[str, Any] = {}


class ChatResult(BaseModel):
    """A document returned by a video_chat semantic query."""

    id: str
    score: float
    video_id: str
    role: ChatRole
    content: str
    metadata: dict[str, Any] = {}


# ---------------------------------------------------------------------------
# VideoChat
# ---------------------------------------------------------------------------

COLLECTION_NAME = "video_chat"


class VideoChat:
    """Manages the video_chat zvec collection."""

    def __init__(self, index_path: Path, embedding_dim: int = 768):
        """Initialise the video_chat collection.

        Args:
            index_path: Directory path for this collection (e.g. ~/.atlas/index/video_chat).
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

    async def index_message(
        self,
        video_id: str,
        role: ChatRole,
        content: str,
    ) -> str:
        """Embed and store a single chat message.

        Args:
            video_id: The video this message belongs to.
            role: 'user' or 'assistant'.
            content: Message text.

        Returns:
            Document ID of the inserted message.
        """
        from .text_embedding import embed_text_async

        embedding = await embed_text_async(content, self.embedding_dim)
        doc_id = self._uuid()
        metadata = {"timestamp": datetime.now().isoformat()}
        zvec_doc = _make_doc(doc_id, embedding, video_id, role, content, metadata)
        self.collection.insert([zvec_doc])
        self.collection.flush()
        return doc_id

    async def search(
        self,
        query: str,
        video_id: str,
        top_k: int = 5,
        role: Optional[ChatRole] = None,
    ) -> List[ChatResult]:
        """Semantic search in the chat collection for a specific video.

        Args:
            query: Query text.
            video_id: Restrict to this video's chat history.
            top_k: Maximum results.
            role: Optionally restrict to 'user' or 'assistant' messages.

        Returns:
            List of ChatResult ordered by relevance.
        """
        from .text_embedding import embed_text_async

        query_embedding = await embed_text_async(query, self.embedding_dim)
        try:
            vector_query = _make_vector_query(query_embedding)
            filt = f"video_id == {video_id} AND role == {role}" if role else f"video_id == {video_id}"
            results = self.collection.query(vector_query, topk=top_k, filter=filt)
        except Exception as e:
            logger.error(f"Error querying video_chat: {e}")
            return []

        return [
            ChatResult(
                id=r.id,
                score=r.score or 0,
                video_id=r.field("video_id"),  # type: ignore[arg-type]
                role=r.field("role"),  # type: ignore[arg-type]
                content=r.field("content"),  # type: ignore[arg-type]
                metadata=json.loads(r.field("metadata")),  # type: ignore[arg-type]
            )
            for r in results
        ]

    @property
    def stats(self) -> Any:
        """Raw zvec collection stats."""
        return self.collection.stats
