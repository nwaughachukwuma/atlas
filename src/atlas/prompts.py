"""
Prompts for video analysis
"""

from dataclasses import dataclass
from typing import List, Literal, Optional, cast

from pydantic import BaseModel

from .utils import DescriptionAttr, VideoAttrAnalysis


@dataclass
class VideoPrompt:
    """Video analysis prompt"""

    value: str
    attr: DescriptionAttr

    def __str__(self) -> str:
        return self.value


VideoAnalysisDescriptionAttr = Literal[
    "visual_cues",
    "audio_analysis",
    "interactions",
    "contextual_information",
]


class VideoAnalysisSchema(BaseModel):
    visual_cues: Optional[str] = None
    audio_analysis: Optional[str] = None
    interactions: Optional[str] = None
    contextual_information: Optional[str] = None

    def _to_attr_list(self) -> list[VideoAttrAnalysis]:
        return [
            VideoAttrAnalysis(attr=cast(DescriptionAttr, k), value=v or "")
            for k, v in self.model_dump().items()
            if k in VideoAnalysisDescriptionAttr.__args__
        ]


def video_system_prompt(req_prompt: str, attrs: List[DescriptionAttr]) -> str:
    """Generate system prompt for video analysis"""
    attrs_label = ", ".join(" ".join(attr.upper().split("_")) for attr in attrs)
    return f"""You are an advanced media agent capable of providing accurate and concise
description of a video (or audio) based on its content and overall makeup.

Your task is to generate a highly detailed and semantically rich, clear and precise
description of the media capturing the main points and key details, based the following:

Request:
    - Guideline:{req_prompt}
    - Available Attributes: {attrs_label} 
    - Omit any key/attribute that's not in the list of Available Attributes above

Important Information:
    - Be exhaustive in capturing discriminative visual, auditory, textual or
      contextual signals.
    - Anchor key observations within 3 seconds window. If something evolves,
      describe its trajectory or change.
    - Focus on WHAT IS HAPPENING and HOW it's happening, not just what objects
      are present.

No preambles, just the JSON response
"""


def summarize_descriptions_prompt(video_descriptions: str) -> str:
    """Generate prompt for summarizing video descriptions"""
    return f"""You're an advanced language model tasked with summarizing a collection of
video descriptions comprising the audio analysis, visual cues, contextual
information, transcript and interactions.

You will provide one paragraph summary capturing major details and preserving
the underlying information and context.

Your summary must be highly detailed, temporally anchored, and semantically
rich, clear and precise.

The Video Descriptions:
{video_descriptions}

Provide no preambles, just the summary.
"""


def chat_system_prompt(
    video_context: list[str],
    chat_history: list[dict],
    extra_context: list[str],
) -> str:
    """System prompt for the video chat command.

    Args:
        video_context: Top-k multimodal insight snippets from video_index.
        chat_history: Ordered list of past messages (dicts with role/content).
        extra_context: Semantically similar chat entries, deduped from history.

    Returns:
        A fully formatted system instruction string.
    """
    video_ctx_block = "\n\n".join(f"- {s}" for s in video_context) if video_context else "(none)"

    history_lines: list[str] = []
    for msg in chat_history:
        role = msg.get("role", "user").capitalize()
        content = msg.get("content", "")
        history_lines.append(f"{role}: {content}")
    history_block = "\n".join(history_lines) if history_lines else "(no prior conversation)"

    extra_block = "\n\n".join(f"- {s}" for s in extra_context) if extra_context else "(none)"

    return f"""You are Atlas, an intelligent video assistant. You help users understand and explore
the content of a video based on multimodal analysis that has already been performed on it.

You have access to the following context:

## Relevant Video Content (semantic search results)
{video_ctx_block}

## Conversation History (up to 20 recent messages)
{history_block}

## Additional Related Context (semantic chat search, new only)
{extra_block}

## Instructions
- Answer the user's question based strictly on the video context provided above.
- Cite specific timestamps or observations when available.
- If the context doesn't contain enough information to answer, say so honestly.
- Keep responses concise and focused. Do not hallucinate details.
- Refer to the conversation history to maintain continuity.
"""


video_analysis_prompt = """Analyze the video and return a JSON object with exactly these four keys/attributes.
Each value must be a detailed string and be within 240 characters.

{
  "visual_cues": "Describe every visible entity (people, objects, animals, structures) by name/identity,
    appearance (color, texture, size, clothing, posture), location, spatial composition, and arrangement.
    Track motion trajectories and state changes over time. For creative/instructional content, describe
    the work being created and how it evolves (e.g. 'canvas transitions from blank to blue wash').
    For demonstrations, identify tools, materials, and supplies in use. Capture faces, brands, logos,
    landmarks, and salient visual features.",

  "audio_analysis": "Describe all audio characteristics. Speech: speaker identity, emotion, clarity,
    pace, and acoustic qualities (reverb, distortion, volume shifts). Music: genre, tempo,
    instrumentation, key, and emotional tone. Sound effects: type, source, and intensity. Ambient
    noise: crowd, wind, machinery, etc. Note how audio contributes to the overall mood or narrative.",

  "interactions": "Describe dynamic interactions between entities: movements, gestures, facial expressions,
    body language, gaze direction, proximity changes, interpersonal dynamics, and implied intent. Capture
    how relationships evolve (e.g. 'Person A approaches Person B, who turns away then smiles'). For
    instructional content, explain what is being done and how — specific techniques, steps, and
    cause-and-effect relationships (e.g. 'applying pressure causes paint to spread'). For processes,
    note sequential actions building toward an outcome (e.g. 'applies base layer, then blends edges
    while still wet').",

  "contextual_information": "Detail production and contextual elements. Camera: movements (pan, zoom,
    static), framing (close-up, wide, over-the-shoulder). Transitions and scene changes. Lighting:
    quality, direction, conditions (e.g. 'stage spotlight', 'front-left fill'). Setting: indoor/outdoor,
    formal/casual, time of day, weather, background ambiance. Stylistic choices: slow-mo, color grading,
    mood and tone. On-screen text, OCR, overlays, logos, and graphics."
}

Return only valid JSON. No markdown, no explanation outside the JSON object.
"""

transcription_prompt = (
    """Provide a verbatim transcript of all spoken content:
- Capture every word exactly as said, including filler words (um, uh, like)
- Label multiple speakers (e.g., "Speaker 1: ...", "Speaker 2: ...")
- Mark pauses with [pause] and inaudible portions with [inaudible]
- Preserve natural flow and grammatical irregularities; minimal punctuation

If no speech is present, respond with: [No speech detected]""",
)
