import asyncio
import json
import logging
import os
import signal
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field

from config import Config
from i18n import t

log = logging.getLogger(__name__)

# Callback types
ToolCallback = Callable[[str, str], Coroutine]  # (tool_name, summary)
TextCallback = Callable[[str], Coroutine]  # (accumulated_text)
IntermediateCallback = Callable[[str], Coroutine]  # (completed_text_block)

# Safety: max time a Claude process can run (30 min)
_MAX_PROCESS_TIME = 30 * 60


@dataclass
class ClaudeResult:
    text: str
    session_id: str | None
    cost_usd: float | None
    is_error: bool
    tools_used: list[str] = field(default_factory=list)


# Active processes per thread_id — used by /cancel
_active_procs: dict[int, asyncio.subprocess.Process] = {}


def get_active_proc(thread_id: int) -> asyncio.subprocess.Process | None:
    return _active_procs.get(thread_id)


def _kill_tree(proc: asyncio.subprocess.Process):
    """Kill process and all its children via process group."""
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError):
        try:
            proc.kill()
        except ProcessLookupError:
            pass


async def run_claude(
    prompt: str,
    project_path: str,
    config: Config,
    session_id: str | None = None,
    on_tool: ToolCallback | None = None,
    on_text: TextCallback | None = None,
    on_intermediate: IntermediateCallback | None = None,
    thread_id: int | None = None,
    model: str | None = None,
) -> ClaudeResult:
    """Run `claude -p` with stream-json to capture tool usage and text in real time."""

    cmd = [
        config.claude_cli_path,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--verbose",
        "--include-partial-messages",
        "--max-budget-usd",
        str(config.max_budget_usd),
        "--permission-mode",
        config.permission_mode,
    ]

    if model:
        cmd += ["--model", model]

    if session_id:
        cmd += ["--resume", session_id]

    for tool in config.allowed_tools:
        cmd += ["--allowedTools", tool]

    # Remove CLAUDECODE to avoid nested session conflict
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}

    log.info("Running claude in %s (session=%s)", project_path, session_id or "new")

    proc = await asyncio.create_subprocess_exec(
        *cmd,
        cwd=project_path,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=env,
        limit=10 * 1024 * 1024,  # 10 MB line buffer (default 64KB too small)
        start_new_session=True,  # own process group — kill takes all children
    )

    # Register for /cancel
    if thread_id is not None:
        _active_procs[thread_id] = proc

    try:
        result_text, new_session_id, cost, is_error, tools_used = await asyncio.wait_for(
            _read_stream(proc, session_id, on_tool, on_text, on_intermediate),
            timeout=_MAX_PROCESS_TIME,
        )
    except asyncio.TimeoutError:
        log.warning("Claude process timed out after %d sec, killing", _MAX_PROCESS_TIME)
        _kill_tree(proc)
        await proc.wait()
        return ClaudeResult(
            text=t("process_timeout", minutes=_MAX_PROCESS_TIME // 60),
            session_id=session_id,
            cost_usd=None,
            is_error=True,
        )
    except asyncio.CancelledError:
        _kill_tree(proc)
        await proc.wait()
        return ClaudeResult(
            text=t("request_cancelled"),
            session_id=session_id,
            cost_usd=None,
            is_error=True,
        )
    finally:
        # Always clean up: kill any remaining children
        _kill_tree(proc)
        if thread_id is not None:
            _active_procs.pop(thread_id, None)

    # If process failed and we got nothing useful, read stderr
    if proc.returncode and proc.returncode != 0 and not result_text:
        stderr = ""
        if proc.stderr:
            stderr_bytes = await proc.stderr.read()
            stderr = stderr_bytes.decode(errors="replace").strip()
        error_text = stderr or t("exit_code", code=proc.returncode)
        log.error("Claude failed: %s", error_text)
        return ClaudeResult(
            text=t("claude_error", error=error_text[:3000]),
            session_id=session_id,
            cost_usd=None,
            is_error=True,
            tools_used=tools_used,
        )

    return ClaudeResult(
        text=result_text or "(empty response)",
        session_id=new_session_id,
        cost_usd=cost,
        is_error=is_error,
        tools_used=tools_used,
    )


async def _read_stream(
    proc: asyncio.subprocess.Process,
    session_id: str | None,
    on_tool: ToolCallback | None,
    on_text: TextCallback | None,
    on_intermediate: IntermediateCallback | None = None,
) -> tuple[str, str | None, float | None, bool, list[str]]:
    """Read stream-json lines from stdout, parse events."""
    result_text = ""
    new_session_id = session_id
    cost = None
    is_error = False
    tools_used: list[str] = []
    text_parts: list[str] = []
    streaming_text = ""  # accumulated text from deltas

    async for raw_line in proc.stdout:
        line = raw_line.decode(errors="replace").strip()
        if not line:
            continue

        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue

        ev_type = event.get("type", "")

        # --- Result message (final) ---
        if ev_type == "result":
            result_text = event.get("result", "") or ""
            new_session_id = event.get("session_id") or session_id
            cost = event.get("cost_usd")
            is_error = event.get("is_error", False)
            # Got the result — stop reading immediately.
            # Child processes may keep stdout open, don't wait for them.
            break

        # --- Streaming text delta ---
        elif ev_type == "stream_event":
            delta = event.get("event", {}).get("delta", {})
            if delta.get("type") == "text_delta":
                chunk = delta.get("text", "")
                if chunk:
                    streaming_text += chunk
                    if on_text:
                        try:
                            await on_text(streaming_text)
                        except Exception:
                            pass

        # --- Assistant message with content blocks ---
        elif ev_type == "assistant":
            msg = event.get("message", {})
            for block in msg.get("content", []):
                block_type = block.get("type", "")

                if block_type == "tool_use":
                    tool_name = block.get("name", "unknown")
                    tool_input = block.get("input", {})
                    summary = _tool_summary(tool_name, tool_input)
                    tools_used.append(summary)
                    # Send intermediate text before resetting
                    if streaming_text.strip() and on_intermediate:
                        try:
                            await on_intermediate(streaming_text.strip())
                        except Exception:
                            pass
                    streaming_text = ""
                    if on_tool:
                        try:
                            await on_tool(tool_name, summary)
                        except Exception:
                            pass

                elif block_type == "text":
                    txt = block.get("text", "")
                    if txt:
                        text_parts.append(txt)

        # --- System init message ---
        elif ev_type == "system":
            sid = event.get("session_id")
            if sid:
                new_session_id = sid

    # If no result was given, combine text parts
    if not result_text and text_parts:
        result_text = "\n".join(text_parts)

    return result_text, new_session_id, cost, is_error, tools_used


def _tool_summary(name: str, input_data: dict) -> str:
    """Build a short human-readable summary of a tool call."""
    if name == "Read":
        return f"Read: {input_data.get('file_path', '?')}"
    if name == "Write":
        return f"Write: {input_data.get('file_path', '?')}"
    if name == "Edit":
        return f"Edit: {input_data.get('file_path', '?')}"
    if name == "Bash":
        cmd = input_data.get("command", "?")
        return f"Bash: {cmd[:60]}"
    if name == "Glob":
        return f"Glob: {input_data.get('pattern', '?')}"
    if name == "Grep":
        return f"Grep: {input_data.get('pattern', '?')}"
    if name == "Task":
        return f"Task: {input_data.get('description', '?')}"
    return f"{name}"
