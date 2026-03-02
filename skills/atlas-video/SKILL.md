```skill
---
name: atlas-video
description: Skills for atlas-video — a multimodal video understanding engine and its Remotion product-video project
metadata:
  tags: atlas, atlas-video, video, multimodal, gemini, groq, remotion, cli, python, docker
---

## When to use

Use this skill whenever you need to:
- Extract multimodal insights (visual cues, audio analysis, transcripts, etc.) from videos using Atlas
- Index videos for semantic search and chat using the Atlas CLI, Python API, or HTTP server
- Build or extend the Remotion-based `product-video` project that showcases Atlas features

## What is atlas-video

Atlas is an open-source multimodal insights engine for video understanding. It uses Google Gemini for multimodal analysis and embeddings, and Groq Whisper for fast transcription. All indexed data is stored locally in a zvec vector store at `~/.atlas/index`.

## How to use these rules

Read individual rule files for detailed guidance and code examples:

- [rules/overview.md](rules/overview.md) — Architecture, vector store layout, environment variables, and performance numbers
- [rules/cli-commands.md](rules/cli-commands.md) — All CLI commands: extract, index, search, chat, transcribe, get-video, list-videos, list-chat, stats, queue, serve
- [rules/python-api.md](rules/python-api.md) — Programmatic Python API: VideoProcessor, index_video, search_video, chat_with_video, extract_transcript
- [rules/http-api.md](rules/http-api.md) — HTTP server endpoints exposed by `atlas serve`, including streaming chat via SSE
- [rules/docker.md](rules/docker.md) — Docker usage: one-liner commands, env vars, named volumes, serving behind a reverse proxy
- [rules/product-video-structure.md](rules/product-video-structure.md) — Remotion product-video project layout, Root composition, scene durations, and render commands
- [rules/product-video-scenes.md](rules/product-video-scenes.md) — All 8 scenes (Hero, Features, Extract, IndexSearch, Chat, Transcribe, Performance, CTA), their purpose and animation patterns
- [rules/product-video-components.md](rules/product-video-components.md) — Shared components: Background, TerminalWindow, FadeSlideIn, ScaleIn, GlowText, Typewriter, SectionLabel
- [rules/product-video-theme.md](rules/product-video-theme.md) — Design tokens: COLORS palette, FONTS, and how to apply them consistently
```
