import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import yaml


def _default_claude_path() -> str:
    """Find claude CLI in PATH or common locations."""
    found = shutil.which("claude")
    if found:
        return found
    home = Path.home()
    for candidate in [
        home / ".local" / "bin" / "claude",
        home / ".claude" / "local" / "claude",
        Path("/usr/local/bin/claude"),
    ]:
        if candidate.exists():
            return str(candidate)
    return "claude"


def _default_projects_root() -> str:
    return str(Path.home() / "projects")


@dataclass
class Config:
    telegram_bot_token: str = ""
    allowed_user_ids: list[int] = field(default_factory=list)
    claude_cli_path: str = field(default_factory=_default_claude_path)
    permission_mode: str = "bypassPermissions"
    allowed_tools: list[str] = field(
        default_factory=lambda: ["Bash", "Read", "Write", "Edit", "Glob", "Grep"]
    )
    max_budget_usd: float = 5.0
    projects_root: str = field(default_factory=_default_projects_root)
    max_depth: int = 5
    sessions_file: str = "sessions.json"
    max_message_length: int = 4000
    language: str = "en"


def load_config(path: str | None = None) -> Config:
    if path is None:
        path = str(Path(__file__).parent / "config.yaml")

    data = {}
    if os.path.exists(path):
        with open(path) as f:
            data = yaml.safe_load(f) or {}

    # Env overrides
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        data["telegram_bot_token"] = os.environ["TELEGRAM_BOT_TOKEN"]
    if os.environ.get("ALLOWED_USER_IDS"):
        data["allowed_user_ids"] = [
            int(x.strip()) for x in os.environ["ALLOWED_USER_IDS"].split(",")
        ]
    if os.environ.get("CLAUDE_CLI_PATH"):
        data["claude_cli_path"] = os.environ["CLAUDE_CLI_PATH"]
    if os.environ.get("PROJECTS_ROOT"):
        data["projects_root"] = os.environ["PROJECTS_ROOT"]

    # Backward compat: single allowed_user_id → list
    if "allowed_user_id" in data and "allowed_user_ids" not in data:
        uid = data.pop("allowed_user_id")
        if uid:
            data["allowed_user_ids"] = [int(uid)]
    elif "allowed_user_id" in data:
        data.pop("allowed_user_id")

    # Filter out unknown keys
    known = {f.name for f in Config.__dataclass_fields__.values()}
    filtered = {k: v for k, v in data.items() if k in known}

    return Config(**filtered)
