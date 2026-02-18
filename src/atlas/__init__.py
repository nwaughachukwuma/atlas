"""
Atlas - A multimodal insights engine for video understanding
"""

__version__ = "0.1.0"


# Lazy imports to avoid loading heavy dependencies at import time
# These are only loaded when actually needed (e.g., when running CLI commands)
def __getattr__(name):
    if name == "TextEmbedding":
        from .text_embedding import TextEmbedding

        return TextEmbedding
    elif name == "VectorStore":
        from .vector_store import VectorStore

        return VectorStore
    elif name == "VideoProcessor":
        from .video_processor import VideoProcessor

        return VideoProcessor
    elif name == "VideoProcessorConfig":
        from .video_processor import VideoProcessorConfig

        return VideoProcessorConfig
    elif name == "VideoProcessorResult":
        from .video_processor import VideoProcessorResult

        return VideoProcessorResult
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
