"""
atlas.vector_store — vector index package for Atlas.

Structure
---------
base.py        BaseCollection — shared zvec lifecycle and helpers
video_index.py VideoIndex     — multimodal segment embeddings + registry
video_chat.py  VideoChat      — per-video chat history embeddings + JSONL sidecar

All public symbols are re-exported here so callers can use either:
    from atlas.vector_store import VideoIndex, SearchResult
    from atlas.vector_store.video_index import VideoIndex, index_video
"""

from .video_chat import (
    COLLECTION_NAME as CHAT_COLLECTION_NAME,
    ChatDocument,
    ChatResult,
    ChatRole,
    VideoChat,
)
from .video_index import (
    COLLECTION_NAME as VIDEO_COLLECTION_NAME,
    IndexDocument,
    SearchResult,
    VideoEntry,
    VideoIndex,
    index_video,
    search_video,
)

__all__ = [
    # video_index
    "VideoIndex",
    "IndexDocument",
    "SearchResult",
    "VideoEntry",
    "index_video",
    "search_video",
    # video_chat
    "VideoChat",
    "ChatDocument",
    "ChatResult",
    "ChatRole",
    # collection name constants
    "VIDEO_COLLECTION_NAME",
    "CHAT_COLLECTION_NAME",
]
