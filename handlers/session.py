import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from claude_bridge.runner import _kill_tree, get_active_proc
from claude_bridge.session_store import SessionStore
from i18n import t
from utils.auth import authorized_only


@authorized_only
async def new_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text(t("use_in_topic"))
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text(t("not_bound"))
        return

    session_store.clear_session(thread_id)
    folder = os.path.basename(info.project_path)
    await update.message.reply_text(
        f"🔄 {t('new_session', folder=folder)}", parse_mode="HTML"
    )


@authorized_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text(t("use_in_topic"))
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text(t("not_bound"))
        return

    sid = info.session_id
    sid_display = f"<code>{sid[:16]}...</code>" if sid else t("none")
    folder = os.path.basename(info.project_path)
    model_display = info.model or t("no_model")

    await update.message.reply_text(
        t("status_project", folder=folder, path=info.project_path,
          model=model_display, session=sid_display),
        parse_mode="HTML",
    )


@authorized_only
async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text(t("use_in_topic"))
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text(t("not_bound"))
        return

    sessions = SessionStore.list_sessions(info.project_path)
    if not sessions:
        await update.message.reply_text(t("no_sessions"))
        return

    sess_map: dict[str, str] = {}
    context.user_data["sess_map"] = sess_map

    buttons: list[list[InlineKeyboardButton]] = []
    for i, s in enumerate(sessions[:15]):
        idx = str(i)
        sess_map[idx] = s.session_id
        label = s.display[:40]
        if len(s.display) > 40:
            label += "..."
        buttons.append(
            [
                InlineKeyboardButton(
                    f"📝 {s.date_str}  {label}",
                    callback_data=f"sess:{idx}",
                )
            ]
        )

    folder = os.path.basename(info.project_path)
    current = info.session_id
    current_display = t("sessions_active", sid=current[:12]) if current else ""
    header = t("sessions_title", folder=folder, current=current_display)

    await update.message.reply_text(
        f"{header}\n\n{t('pick_session')}",
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


@authorized_only
async def session_pick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    idx = query.data.split(":")[1]
    sess_map: dict[str, str] = context.user_data.get("sess_map", {})
    session_id = sess_map.get(idx)
    if not session_id:
        await query.edit_message_text(t("session_not_found"))
        return

    thread_id = query.message.message_thread_id
    if not thread_id:
        await query.edit_message_text(t("cant_detect_topic"))
        return

    session_store: SessionStore = context.bot_data["session_store"]
    session_store.set_session_id(thread_id, session_id)

    await query.edit_message_text(
        f"✅ {t('session_resumed', sid=session_id[:12])}",
        parse_mode="HTML",
    )


MODELS = [
    ("sonnet", "model_sonnet"),
    ("opus", "model_opus"),
    ("haiku", "model_haiku"),
]


@authorized_only
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text(t("use_in_topic"))
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text(t("not_bound"))
        return

    current = info.model or t("no_model")
    buttons = []
    for alias, desc_key in MODELS:
        mark = " ✓" if alias == info.model else ""
        buttons.append(
            [InlineKeyboardButton(f"{t(desc_key)}{mark}", callback_data=f"model:{alias}")]
        )
    buttons.append(
        [InlineKeyboardButton(
            f"🔄 {t('model_reset_label')}{'  ✓' if not info.model else ''}",
            callback_data="model:reset",
        )]
    )

    await update.message.reply_text(
        t("model_current", model=current),
        reply_markup=InlineKeyboardMarkup(buttons),
        parse_mode="HTML",
    )


@authorized_only
async def model_pick_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice = query.data.split(":")[1]
    thread_id = query.message.message_thread_id
    if not thread_id:
        await query.edit_message_text(t("cant_detect_topic"))
        return

    session_store: SessionStore = context.bot_data["session_store"]

    if choice == "reset":
        session_store.set_model(thread_id, None)
        await query.edit_message_text(f"✅ {t('model_reset_done')}")
    else:
        session_store.set_model(thread_id, choice)
        desc_key = dict(MODELS).get(choice, "")
        desc = t(desc_key) if desc_key else choice
        await query.edit_message_text(
            f"✅ {t('model_set', desc=desc)}",
            parse_mode="HTML",
        )


@authorized_only
async def tools_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = context.bot_data.get("show_tools", True)
    context.bot_data["show_tools"] = not current
    state = t("tools_on") if not current else t("tools_off")
    await update.message.reply_text(
        f"🔧 {t('tools_toggle', state=state)}", parse_mode="HTML"
    )


@authorized_only
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text(t("use_in_topic"))
        return

    proc = get_active_proc(thread_id)
    if not proc:
        await update.message.reply_text(t("nothing_running"))
        return

    _kill_tree(proc)
    await update.message.reply_text(f"🛑 {t('cancelled')}")
