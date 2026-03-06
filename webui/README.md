# Atlas Web UI

This directory contains the Svelte 5 Web UI for Atlas Video. In production, the built assets are served by the Atlas HTTP server under `/ui`.

## What it supports

The Web UI is a browser companion to the Atlas Docker/server workflow. It currently provides pages for:

- dashboard and health overview
- transcription
- multimodal extraction
- video indexing
- indexed video browsing and per-video detail views
- chat history and video chat
- task queue monitoring

Routes are mounted under `/ui`, including:

- `/ui`
- `/ui/transcribe`
- `/ui/extract`
- `/ui/index`
- `/ui/videos`
- `/ui/video/:id`
- `/ui/queue`
- `/ui/dashboard`

## Production workflow

Users do not need Node.js or the Vite dev server to use the Web UI. After pulling the Docker image, start Atlas and open the browser:

```bash
docker run -p 8000:8000 -it \
	-v atlas-data:/home/atlas/.atlas \
	--env-file .env \
	nwaughachukwuma/atlas-video
```

Then visit:

```text
http://localhost:8000/ui
```

The UI talks to the Atlas server on the same host and uses the same REST API exposed on port `8000`.

## Local development

For contributors working on the frontend itself:

```bash
cd webui
npm install
npm run dev
```

Useful scripts:

- `npm run dev` starts the Vite development server
- `npm run build` builds production assets
- `npm run watch` rebuilds on file changes
- `npm run preview` previews the production build
- `npm run check` runs `svelte-check`

## Backend expectations

The frontend expects the Atlas server to expose these endpoints on `http://localhost:8000`:

- `POST /transcribe`
- `POST /extract`
- `POST /index`
- `POST /search`
- `POST /chat`
- `GET /health`
- `GET /list-videos`
- `GET /get-video/:video_id`
- `GET /list-chat/:video_id`
- `GET /stats`
- `GET /queue/list`
- `GET /queue/status/:task_id`

## Notes

- Persistent vector data should be mounted to `/home/atlas/.atlas` in Docker.
- The Web UI is bundled with the main Atlas image; it is not a separate deployable service.
