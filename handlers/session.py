import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from claude_bridge.runner import _kill_tree, get_active_proc
from claude_bridge.session_store import SessionStore
from utils.auth import authorized_only


@authorized_only
async def new_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text("Используй эту команду внутри топика проекта.")
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text("Этот топик не привязан к проекту.")
        return

    session_store.clear_session(thread_id)
    folder = os.path.basename(info.project_path)
    await update.message.reply_text(
        f"🔄 Новая сессия для <b>{folder}</b>.\nПиши первое сообщение.",
        parse_mode="HTML",
    )


@authorized_only
async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text("Используй эту команду внутри топика проекта.")
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text("Этот топик не привязан к проекту.")
        return

    sid = info.session_id
    sid_display = f"<code>{sid[:16]}...</code>" if sid else "нет"
    folder = os.path.basename(info.project_path)
    model_display = info.model or "по умолчанию"

    await update.message.reply_text(
        f"<b>Проект:</b> {folder}\n"
        f"<b>Путь:</b> <code>{info.project_path}</code>\n"
        f"<b>Модель:</b> {model_display}\n"
        f"<b>Сессия:</b> {sid_display}",
        parse_mode="HTML",
    )


@authorized_only
async def sessions_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text("Используй эту команду внутри топика проекта.")
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text("Этот топик не привязан к проекту.")
        return

    sessions = SessionStore.list_sessions(info.project_path)
    if not sessions:
        await update.message.reply_text("Сессий для этого проекта не найдено.")
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
    current_display = f"\nАктивная: <code>{current[:12]}...</code>" if current else ""

    await update.message.reply_text(
        f"<b>Сессии {folder}</b>{current_display}\n\n"
        "Выбери сессию для продолжения:",
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
        await query.edit_message_text("Сессия не найдена. Попробуй /sessions заново.")
        return

    thread_id = query.message.message_thread_id
    if not thread_id:
        await query.edit_message_text("Не удалось определить топик.")
        return

    session_store: SessionStore = context.bot_data["session_store"]
    session_store.set_session_id(thread_id, session_id)

    await query.edit_message_text(
        f"✅ Продолжаем сессию <code>{session_id[:12]}...</code>\n"
        "Пиши сообщение.",
        parse_mode="HTML",
    )


MODELS = [
    ("sonnet", "Sonnet — быстрый и дешёвый"),
    ("opus", "Opus — самый умный"),
    ("haiku", "Haiku — самый быстрый"),
]


@authorized_only
async def model_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text("Используй эту команду внутри топика проекта.")
        return

    session_store: SessionStore = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await update.message.reply_text("Этот топик не привязан к проекту.")
        return

    current = info.model or "по умолчанию"
    buttons = []
    for alias, desc in MODELS:
        mark = " ✓" if alias == info.model else ""
        buttons.append(
            [InlineKeyboardButton(f"{desc}{mark}", callback_data=f"model:{alias}")]
        )
    buttons.append(
        [InlineKeyboardButton(
            f"🔄 Сбросить (по умолчанию){'  ✓' if not info.model else ''}",
            callback_data="model:reset",
        )]
    )

    await update.message.reply_text(
        f"<b>Текущая модель:</b> {current}\n\nВыбери модель для этого проекта:",
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
        await query.edit_message_text("Не удалось определить топик.")
        return

    session_store: SessionStore = context.bot_data["session_store"]

    if choice == "reset":
        session_store.set_model(thread_id, None)
        await query.edit_message_text(
            "✅ Модель сброшена — будет использоваться модель по умолчанию.",
        )
    else:
        session_store.set_model(thread_id, choice)
        desc = dict(MODELS).get(choice, choice)
        await query.edit_message_text(
            f"✅ Модель: <b>{desc}</b>",
            parse_mode="HTML",
        )


@authorized_only
async def tools_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current = context.bot_data.get("show_tools", True)
    context.bot_data["show_tools"] = not current
    state = "ВКЛ" if not current else "ВЫКЛ"
    await update.message.reply_text(f"🔧 Отображение тулов: <b>{state}</b>", parse_mode="HTML")


@authorized_only
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text("Используй эту команду внутри топика проекта.")
        return

    proc = get_active_proc(thread_id)
    if not proc:
        await update.message.reply_text("Сейчас ничего не выполняется.")
        return

    _kill_tree(proc)
    await update.message.reply_text("🛑 Запрос отменён.")
