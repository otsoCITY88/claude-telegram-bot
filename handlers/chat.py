import asyncio
import logging
import tempfile
import time

from telegram import Message
from telegram.ext import ContextTypes

from claude_bridge.runner import run_claude
from i18n import t
from utils.auth import authorized_only
from utils.formatting import claude_to_telegram_html, escape_html
from utils.message_splitter import split_message

log = logging.getLogger(__name__)

_processing: set[int] = set()
_EDIT_COOLDOWN = 1.5


@authorized_only
async def handle_message(update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    thread_id = message.message_thread_id

    if not thread_id:
        await message.reply_text(t("use_topic"))
        return

    session_store = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await message.reply_text(t("topic_not_bound"))
        return

    await send_to_claude(message, message.text, context)


async def send_to_claude(
    message: Message,
    prompt: str,
    context: ContextTypes.DEFAULT_TYPE,
):
    """Core function: send prompt to Claude and stream the response.

    Called by handle_message, handle_file, handle_voice.
    """
    thread_id = message.message_thread_id
    session_store = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    config = context.bot_data["config"]
    show_tools = context.bot_data.get("show_tools", True)

    if thread_id in _processing:
        await message.reply_text(t("still_processing"))
        return

    _processing.add(thread_id)

    thinking = await message.reply_text(f"🔄 {t('thinking')}")

    start_time = time.monotonic()
    last_edit = start_time
    tool_log: list[str] = []
    last_status = ""
    streaming_active = False

    async def _edit(text: str):
        nonlocal last_edit, last_status
        now = time.monotonic()
        if text == last_status or (now - last_edit) < _EDIT_COOLDOWN:
            return
        last_status = text
        last_edit = now
        try:
            await thinking.edit_text(text, parse_mode="HTML")
        except Exception:
            try:
                await thinking.edit_text(text)
            except Exception:
                pass

    async def _on_tool(tool_name: str, summary: str):
        nonlocal streaming_active
        if not show_tools:
            return
        streaming_active = False
        tool_log.append(summary)
        elapsed = int(time.monotonic() - start_time)
        lines = tool_log[-5:]
        tools_text = "\n".join(f"  <code>{escape_html(l)}</code>" for l in lines)
        await _edit(f"🔄 {t('working', elapsed=elapsed)}\n\n🔧 <b>{t('tools_label')}</b>\n{tools_text}")

    async def _on_text(accumulated: str):
        nonlocal streaming_active
        streaming_active = True
        preview = accumulated[-300:] if len(accumulated) > 300 else accumulated
        if len(accumulated) > 300:
            preview = "..." + preview
        elapsed = int(time.monotonic() - start_time)
        await _edit(f"💬 {t('writing', elapsed=elapsed)}\n\n{escape_html(preview)}")

    async def _on_intermediate(text: str):
        nonlocal streaming_active
        streaming_active = False
        formatted = claude_to_telegram_html(text)
        chunks = split_message(formatted, config.max_message_length)
        for chunk in chunks:
            await _safe_send(message, chunk)

    async def _tick():
        while True:
            await asyncio.sleep(5)
            if streaming_active:
                continue
            elapsed = int(time.monotonic() - start_time)
            if show_tools and tool_log:
                lines = tool_log[-5:]
                tools_text = "\n".join(f"  <code>{escape_html(l)}</code>" for l in lines)
                await _edit(f"🔄 {t('working', elapsed=elapsed)}\n\n🔧 <b>{t('tools_label')}</b>\n{tools_text}")
            else:
                await _edit(f"🔄 {t('claude_working', elapsed=elapsed)}")

    ticker = asyncio.create_task(_tick())

    try:
        result = await run_claude(
            prompt=prompt,
            project_path=info.project_path,
            config=config,
            session_id=info.session_id,
            on_tool=_on_tool,
            on_text=_on_text,
            on_intermediate=_on_intermediate,
            thread_id=thread_id,
            model=info.model,
        )

        if result.session_id:
            session_store.set_session_id(thread_id, result.session_id)

        try:
            await thinking.delete()
        except Exception:
            pass

        if show_tools and result.tools_used:
            tools_text = "\n".join(f"  <code>{escape_html(s)}</code>" for s in result.tools_used)
            if len(tools_text) > config.max_message_length - 100:
                tools_text = tools_text[: config.max_message_length - 120] + "\n  ..."
            await _safe_send(
                message,
                f"🔧 <b>{t('tools_used', count=len(result.tools_used))}</b>\n{tools_text}",
            )

        formatted = claude_to_telegram_html(result.text)
        chunks = split_message(formatted, config.max_message_length)

        if len(chunks) <= 10:
            for chunk in chunks:
                await _safe_send(message, chunk)
        else:
            for chunk in chunks[:3]:
                await _safe_send(message, chunk)
            await _send_as_file(message, result.text, "response.txt")
            await message.reply_text(t("response_file", chars=len(result.text)))

        if result.cost_usd is not None:
            await message.reply_text(
                f"💰 ${result.cost_usd:.4f}",
                disable_notification=True,
            )

    except Exception as e:
        log.exception("Chat handler error")
        try:
            await thinking.edit_text(t("chat_error", error=str(e)[:500]))
        except Exception:
            pass
    finally:
        ticker.cancel()
        _processing.discard(thread_id)


async def _safe_send(reply_to, text: str):
    try:
        await reply_to.reply_text(text, parse_mode="HTML")
    except Exception:
        await reply_to.reply_text(text)


async def _send_as_file(reply_to, text: str, filename: str):
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="claude_"
    ) as f:
        f.write(text)
        f.flush()
        await reply_to.reply_document(document=open(f.name, "rb"), filename=filename)
