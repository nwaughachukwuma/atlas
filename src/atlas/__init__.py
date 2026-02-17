"""
Atlas - A multimodal insights engine for video understanding
"""

__version__ = "0.1.0"

from atlas.video_processor import VideoProcessor, VideoProcessorConfig, VideoProcessorResult
from atlas.text_embedding import TextEmbedding
from atlas.vector_store import VectorStore

__all__ = [
    "VideoProcessor",
    "VideoProcessorConfig",
    "VideoProcessorResult",
    "TextEmbedding",
    "VectorStore",
]