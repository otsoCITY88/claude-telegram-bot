import json
import os
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass


@dataclass
class TopicInfo:
    project_path: str
    session_id: str | None = None
    model: str | None = None


@dataclass
class SessionInfo:
    session_id: str
    display: str  # first user message (truncated)
    timestamp: int  # ms since epoch
    project: str

    @property
    def date_str(self) -> str:
        return datetime.fromtimestamp(self.timestamp / 1000).strftime("%d.%m %H:%M")


class SessionStore:
    """Persists thread_id -> (project_path, session_id) mapping."""

    def __init__(self, path: str):
        self._path = Path(path)
        # key: str(thread_id)
        self._data: dict[str, dict] = {}
        self._load()

    # -- persistence --

    def _load(self):
        if self._path.exists():
            try:
                self._data = json.loads(self._path.read_text())
            except (json.JSONDecodeError, OSError):
                self._data = {}

    def _save(self):
        self._path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False))

    # -- public API --

    def get(self, thread_id: int) -> TopicInfo | None:
        entry = self._data.get(str(thread_id))
        if not entry:
            return None
        return TopicInfo(
            project_path=entry["project_path"],
            session_id=entry.get("session_id"),
            model=entry.get("model"),
        )

    def set_project(self, thread_id: int, project_path: str):
        key = str(thread_id)
        existing = self._data.get(key, {})
        existing["project_path"] = project_path
        self._data[key] = existing
        self._save()

    def set_session_id(self, thread_id: int, session_id: str):
        key = str(thread_id)
        if key not in self._data:
            return
        self._data[key]["session_id"] = session_id
        self._save()

    def set_model(self, thread_id: int, model: str | None):
        key = str(thread_id)
        if key not in self._data:
            return
        if model:
            self._data[key]["model"] = model
        else:
            self._data[key].pop("model", None)
        self._save()

    def clear_session(self, thread_id: int):
        key = str(thread_id)
        if key in self._data:
            self._data[key].pop("session_id", None)
            self._save()

    # -- session discovery from Claude Code history --

    @staticmethod
    def list_sessions(project_path: str) -> list[SessionInfo]:
        """List all Claude Code sessions for a given project path.

        Reads ~/.claude/history.jsonl and deduplicates by session_id,
        keeping the first (earliest) entry per session as the display text.
        """
        history_file = Path.home() / ".claude" / "history.jsonl"
        if not history_file.exists():
            return []

        # Normalize the project path for matching
        norm_project = os.path.normpath(project_path)

        # Collect first entry per session_id
        seen: dict[str, SessionInfo] = {}
        try:
            for line in history_file.read_text().splitlines():
                if not line.strip():
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                sid = entry.get("sessionId", "")
                proj = os.path.normpath(entry.get("project", ""))
                if proj != norm_project:
                    continue
                if sid in seen:
                    continue
                display = entry.get("display", "").strip()
                # Skip internal commands
                if display.startswith("/") and len(display) < 30:
                    continue
                if not display:
                    display = "(empty)"
                seen[sid] = SessionInfo(
                    session_id=sid,
                    display=display[:80],
                    timestamp=entry.get("timestamp", 0),
                    project=proj,
                )
        except OSError:
            return []

        # Sort by timestamp descending (newest first)
        sessions = sorted(seen.values(), key=lambda s: s.timestamp, reverse=True)
        return sessions
