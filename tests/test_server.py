"""Tests for atlas.server — endpoint signatures, dispatch, and HTTP methods."""

# ruff: noqa: D102

from __future__ import annotations

import io
import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi.testclient import TestClient

from atlas.server import create_app


def _fake_video(name: str = "test.mp4", content: bytes = b"fake-video-data"):
    """Return a (filename, file-like, content-type) tuple for TestClient uploads."""
    return (name, io.BytesIO(content), "video/mp4")


class TestHealthEndpoints:
    def test_health(self):
        client = TestClient(create_app())
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}

    def test_health_includes_execution_time_header(self):
        client = TestClient(create_app())
        resp = client.get("/health")

        assert resp.status_code == 200
        assert "x-execution-time" in resp.headers
        value = resp.headers["x-execution-time"]
        assert value.endswith("ms")
        assert float(value[:-2]) >= 0.0


class TestSearchEndpoint:
    """/search calls the data layer directly and returns structured JSON."""

    def test_search_single_video(self):
        fake_result = MagicMock()
        fake_result.model_dump.return_value = {"segment_id": "seg1", "score": 0.9, "text": "hello"}

        with patch("atlas.vector_store.video_index.search_video", new=AsyncMock(return_value=[fake_result])):
            client = TestClient(create_app())
            resp = client.post("/search", json={"video_id": "vid1", "query": "hello world", "top_k": 3})

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 1
        assert body["results"][0]["segment_id"] == "seg1"

    def test_search_all_videos(self):
        with patch("atlas.vector_store.video_index.search_video", new=AsyncMock(return_value=[])):
            client = TestClient(create_app())
            resp = client.post("/search", json={"query": "hello", "top_k": 5})

        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestChatEndpoint:
    """/chat streams SSE chunks from the data layer."""

    def test_chat_streams_sse(self):
        async def fake_chat(video_id, query):
            yield "Hello "
            yield "world"

        with patch("atlas.chat_handler.chat_with_video", side_effect=fake_chat):
            client = TestClient(create_app())
            resp = client.post("/chat", json={"video_id": "vid1", "query": "What is this?"})

        assert resp.status_code == 200
        assert "text/event-stream" in resp.headers["content-type"]

        events = [line for line in resp.text.splitlines()]
        assert events[0] == "Hello world"


class TestListVideosEndpoint:
    """/list-videos calls the data layer directly."""

    def test_list_videos_returns_structured_json(self):
        fake_video = MagicMock()
        fake_video.model_dump.return_value = {"video_id": "vid1", "title": "Test"}

        fake_index = MagicMock()
        fake_index.list_videos.return_value = [fake_video]

        with patch("atlas.vector_store.video_index.default_video_index", return_value=fake_index):
            client = TestClient(create_app())
            resp = client.get("/list-videos")

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 1
        assert body["videos"][0]["video_id"] == "vid1"

    def test_list_videos_empty(self):
        fake_index = MagicMock()
        fake_index.list_videos.return_value = []

        with patch("atlas.vector_store.video_index.default_video_index", return_value=fake_index):
            client = TestClient(create_app())
            resp = client.get("/list-videos")

        assert resp.status_code == 200
        assert resp.json() == {"count": 0, "videos": []}


class TestListChatEndpoint:
    """/list-chat/{video_id} calls the data layer directly."""

    def test_list_chat_returns_history(self):
        fake_chat = MagicMock()
        fake_chat.get_history.return_value = [
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": "hello"},
        ]

        with patch("atlas.vector_store.video_chat.default_video_chat", return_value=fake_chat):
            client = TestClient(create_app())
            resp = client.get("/list-chat/vid1", params={"last_n": 5})

        assert resp.status_code == 200
        body = resp.json()
        assert body["count"] == 2
        assert len(body["messages"]) == 2
        # confirm last_n is forwarded
        fake_chat.get_history.assert_called_once_with("vid1", last_n=5)


class TestStatsEndpoint:
    """/stats calls both data stores and returns all stat keys."""

    def test_stats_returns_all_keys(self):
        fake_index = MagicMock()
        fake_index.col_path = "/tmp/vi"
        fake_index.stats = "3 videos"
        fake_index.list_videos.return_value = ["a", "b", "c"]

        fake_chat = MagicMock()
        fake_chat.col_path = "/tmp/vc"
        fake_chat.stats = "10 messages"

        with (
            patch("atlas.vector_store.video_index.default_video_index", return_value=fake_index),
            patch("atlas.vector_store.video_chat.default_video_chat", return_value=fake_chat),
        ):
            client = TestClient(create_app())
            resp = client.get("/stats")

        assert resp.status_code == 200
        body = resp.json()
        assert body["video_col_path"] == "/tmp/vi"
        assert body["chat_col_path"] == "/tmp/vc"
        assert body["videos_indexed"] == 3
        assert "video_index_stats" in body
        assert "chat_index_stats" in body


class TestGetVideoEndpoint:
    """/get-video/{video_id} calls the data layer and returns data or 404."""

    def test_get_video_found(self):
        fake_index = MagicMock()
        fake_index.get_video_data.return_value = {"title": "My Video", "duration": 120}

        with patch("atlas.vector_store.video_index.default_video_index", return_value=fake_index):
            client = TestClient(create_app())
            resp = client.get("/get-video/vid1")

        assert resp.status_code == 200
        body = resp.json()
        assert body["data"]["title"] == "My Video"

    def test_get_video_not_found(self):
        fake_index = MagicMock()
        fake_index.get_video_data.return_value = None

        with patch("atlas.vector_store.video_index.default_video_index", return_value=fake_index):
            client = TestClient(create_app())
            resp = client.get("/get-video/missing")

        assert resp.status_code == 404


class TestQueueListEndpoint:
    """/queue/list delegates to the CLI queue command and returns queued tasks."""

    def test_queue_list_no_filter(self):
        from atlas import server as server_module

        def fake_queue_list(_args):
            print(json.dumps({"status_filter": None, "count": 1, "tasks": [{"id": "t1", "status": "pending"}]}))

        with patch.object(server_module, "cmd_queue_list", fake_queue_list):
            client = TestClient(create_app())
            resp = client.get("/queue/list")

        assert resp.status_code == 200
        body = resp.json()
        assert body["status_filter"] is None
        assert body["count"] == 1
        assert body["tasks"][0]["id"] == "t1"

    def test_queue_list_with_status_filter(self):
        from atlas import server as server_module

        captured: dict[str, Any] = {}

        def fake_queue_list(args):
            captured.update(vars(args))
            print(json.dumps({"status_filter": args.status, "count": 0, "tasks": []}))

        with patch.object(server_module, "cmd_queue_list", fake_queue_list):
            client = TestClient(create_app())
            resp = client.get("/queue/list", params={"status": "running"})

        assert resp.status_code == 200
        body = resp.json()
        assert body["status_filter"] == "running"
        assert body["count"] == 0
        assert captured == {"status": "running"}


class TestQueueStatusEndpoint:
    """/queue/status/{task_id} delegates to the CLI queue status command."""

    def test_queue_status_found_no_output(self):
        from atlas import server as server_module

        def fake_queue_status(_args):
            print(json.dumps({"id": "abc123", "status": "completed"}))

        with patch.object(server_module, "cmd_queue_status", fake_queue_status):
            client = TestClient(create_app())
            resp = client.get("/queue/status/abc123")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "abc123"
        assert body["status"] == "completed"

    def test_queue_status_found_with_output_json(self):
        from atlas import server as server_module

        def fake_queue_status(_args):
            print(
                json.dumps(
                    {
                        "id": "abc123",
                        "status": "completed",
                        "output_path": "/tmp/output.json",
                        "benchmark_path": "/tmp/benchmark.txt",
                        "result": {"ok": True, "segments": 3},
                        "benchmark_text": "|...|",
                    }
                )
            )

        with patch.object(server_module, "cmd_queue_status", fake_queue_status):
            client = TestClient(create_app())
            resp = client.get("/queue/status/abc123")

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "abc123"
        assert body["status"] == "completed"
        assert body["output_path"] == "/tmp/output.json"
        assert body["benchmark_path"] == "/tmp/benchmark.txt"
        assert body["result"] == {"ok": True, "segments": 3}
        assert body["benchmark_text"] == "|...|"

    def test_queue_status_not_found(self):
        from atlas import server as server_module

        def fake_queue_status(_args):
            print(json.dumps({"error": "Task missing not found"}))

        with patch.object(server_module, "cmd_queue_status", fake_queue_status):
            client = TestClient(create_app())
            resp = client.get("/queue/status/missing")

        assert resp.status_code == 404


class TestRunsEndpoints:
    def test_runs_list_with_filters(self):
        from atlas import server as server_module

        captured: dict[str, Any] = {}

        def fake_runs_list(args):
            captured.update(vars(args))
            print(json.dumps({"count": 1, "tasks": [{"id": "run1", "run_type": "direct"}]}))

        with patch.object(server_module, "cmd_runs_list", fake_runs_list):
            client = TestClient(create_app())
            resp = client.get("/runs/list", params={"command": "transcribe", "run_type": "direct"})

        assert resp.status_code == 200
        assert resp.json()["tasks"][0]["id"] == "run1"
        assert captured == {"status": None, "command": "transcribe", "run_type": "direct"}

    def test_runs_status_not_found(self):
        from atlas import server as server_module

        def fake_runs_status(_args):
            print(json.dumps({"error": "Run missing not found"}))

        with patch.object(server_module, "cmd_runs_status", fake_runs_status):
            client = TestClient(create_app())
            resp = client.get("/runs/status/missing")

        assert resp.status_code == 404


class TestMediaPostEndpoints:
    """extract/index/transcribe accept file uploads; JSON stdout is auto-parsed."""

    def test_extract_no_queue_returns_json(self, monkeypatch):
        """When --no-queue, cmd_extract prints JSON to stdout; server returns it parsed."""
        from atlas import server as server_module

        def fake_extract(_args):
            print(json.dumps({"segments_count": 5, "video_descriptions": []}))

        monkeypatch.setattr(server_module, "cmd_extract", fake_extract)
        client = TestClient(create_app())
        resp = client.post(
            "/extract",
            files={"video": _fake_video()},
            data={"no_queue": "true"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["segments_count"] == 5

    def test_transcribe_no_queue_returns_json(self, monkeypatch):
        from atlas import server as server_module

        def fake_transcribe(args):
            return {
                "id": "run123",
                "transcript": "Hello world",
                "format": args.format,
                "output_path": "/tmp/output.json",
            }

        monkeypatch.setattr(server_module, "cmd_transcribe", fake_transcribe)
        client = TestClient(create_app())
        resp = client.post(
            "/transcribe",
            files={"video": _fake_video()},
            data={"no_queue": "true", "format": "text"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["id"] == "run123"
        assert body["transcript"] == "Hello world"
        assert body["format"] == "text"
        assert body["output_path"] == "/tmp/output.json"

    def test_extract_queued_returns_structured_run_metadata(self, monkeypatch):
        from atlas import server as server_module

        def fake_extract(args):
            return {
                "task_id": "abc123",
                "id": "abc123",
                "run_type": "queued",
                "output_path": "/tmp/queue/abc123/output.json",
            }

        monkeypatch.setattr(server_module, "cmd_extract", fake_extract)
        client = TestClient(create_app())
        resp = client.post(
            "/extract",
            files={"video": _fake_video()},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["task_id"] == "abc123"
        assert body["run_type"] == "queued"
        assert body["output_path"] == "/tmp/queue/abc123/output.json"

    def test_index_no_queue_returns_json(self, monkeypatch):
        from atlas import server as server_module

        def fake_index(args):
            print(json.dumps({"video_id": "vid1", "video_path": args.video_path, "indexed_count": 10}))

        monkeypatch.setattr(server_module, "cmd_index", fake_index)
        client = TestClient(create_app())
        resp = client.post(
            "/index",
            files={"video": _fake_video()},
            data={"no_queue": "true"},
        )

        assert resp.status_code == 200
        body = resp.json()
        assert body["video_id"] == "vid1"
        assert body["indexed_count"] == 10

    def test_extract_queued_returns_command_result(self, monkeypatch):
        """When queued, output is text confirmation; server wraps it in CommandResult."""
        from atlas import server as server_module

        def fake_extract(args):
            print("Task queued: abc-123")

        monkeypatch.setattr(server_module, "cmd_extract", fake_extract)
        client = TestClient(create_app())
        resp = client.post(
            "/extract",
            files={"video": _fake_video()},
        )

        assert resp.status_code == 200
        body = resp.json()
        # Non-JSON stdout falls back to CommandResult shape
        assert body["ok"] is True
        assert "Task queued" in body["output"]

    def test_extract_defaults_preserved(self, monkeypatch):
        from atlas import server as server_module

        captured: dict[str, Any] = {}

        def fake_extract(args):
            captured.update(vars(args))
            print("done")

        monkeypatch.setattr(server_module, "cmd_extract", fake_extract)
        client = TestClient(create_app())
        client.post(
            "/extract",
            files={"video": _fake_video()},
        )

        assert captured["chunk_duration"] == "15s"
        assert captured["overlap"] == "1s"
        assert captured["no_queue"] is True

    def test_upload_temp_file_cleaned_up(self, monkeypatch):
        """Verify the temp directory created for the upload is removed after the request."""
        from atlas import server as server_module

        saved_path: list[str] = []

        def fake_transcribe(args):
            saved_path.append(args.video_path)
            print(json.dumps({"ok": True}))

        monkeypatch.setattr(server_module, "cmd_transcribe", fake_transcribe)
        client = TestClient(create_app())
        resp = client.post(
            "/transcribe",
            files={"video": _fake_video()},
            data={"no_queue": "true"},
        )

        assert resp.status_code == 200
        # The temp directory should have been cleaned up
        from pathlib import Path

        assert not Path(saved_path[0]).parent.exists()
