import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from utils.auth import authorized_only


def _list_dirs(path: str) -> list[str]:
    try:
        return sorted(
            e
            for e in os.listdir(path)
            if os.path.isdir(os.path.join(path, e)) and not e.startswith(".")
        )
    except PermissionError:
        return []


def _build_keyboard(
    path: str, context: ContextTypes.DEFAULT_TYPE, mode: str
) -> InlineKeyboardMarkup:
    config = context.bot_data["config"]
    path_map: dict[str, str] = context.user_data.setdefault("path_map", {})
    entries = _list_dirs(path)

    buttons: list[list[InlineKeyboardButton]] = []
    for entry in entries:
        full = os.path.join(path, entry)
        idx = str(len(path_map))
        path_map[idx] = full
        buttons.append(
            [InlineKeyboardButton(f"📁 {entry}", callback_data=f"br:{mode}:{idx}")]
        )

    action_row: list[InlineKeyboardButton] = [
        InlineKeyboardButton("📁+ Новая папка", callback_data=f"mkdir:{mode}"),
        InlineKeyboardButton("✅ Выбрать эту", callback_data=f"sel:{mode}"),
    ]
    buttons.append(action_row)

    if os.path.normpath(path) != os.path.normpath(config.projects_root):
        parent = os.path.dirname(path)
        idx = str(len(path_map))
        path_map[idx] = parent
        buttons.append(
            [InlineKeyboardButton("⬆ Назад", callback_data=f"br:{mode}:{idx}")]
        )

    return InlineKeyboardMarkup(buttons)


@authorized_only
async def addproject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    config = context.bot_data["config"]
    context.user_data["browse_path"] = config.projects_root
    context.user_data["path_map"] = {}
    context.user_data.pop("awaiting_folder_name", None)
    kb = _build_keyboard(config.projects_root, context, mode="add")
    await update.message.reply_text(
        f"Обзор: <code>{config.projects_root}</code>", reply_markup=kb, parse_mode="HTML"
    )


@authorized_only
async def setproject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text("Используй эту команду внутри топика.")
        return
    config = context.bot_data["config"]
    context.user_data["browse_path"] = config.projects_root
    context.user_data["path_map"] = {}
    context.user_data["set_thread_id"] = thread_id
    context.user_data.pop("awaiting_folder_name", None)
    kb = _build_keyboard(config.projects_root, context, mode="set")
    await update.message.reply_text(
        f"Обзор: <code>{config.projects_root}</code>", reply_markup=kb, parse_mode="HTML"
    )


@authorized_only
async def browse_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    parts = data.split(":")
    action = parts[0]
    mode = parts[1]

    if action == "br":
        idx = parts[2]
        new_path = context.user_data["path_map"].get(idx)
        if not new_path or not os.path.isdir(new_path):
            await query.edit_message_text("Папка не найдена.")
            return
        context.user_data["browse_path"] = new_path
        context.user_data.pop("awaiting_folder_name", None)
        kb = _build_keyboard(new_path, context, mode)
        await query.edit_message_text(
            f"Обзор: <code>{new_path}</code>", reply_markup=kb, parse_mode="HTML"
        )

    elif action == "mkdir":
        current = context.user_data.get("browse_path", "")
        context.user_data["awaiting_folder_name"] = mode
        await query.edit_message_text(
            f"📁 Создание папки в:\n<code>{current}</code>\n\n"
            "Введи название новой папки:",
            parse_mode="HTML",
        )

    elif action == "sel":
        selected = context.user_data.get("browse_path", "")
        context.user_data.pop("awaiting_folder_name", None)
        session_store = context.bot_data["session_store"]

        if mode == "add":
            folder_name = os.path.basename(selected)
            try:
                topic = await context.bot.create_forum_topic(
                    chat_id=update.effective_chat.id,
                    name=folder_name,
                )
                thread_id = topic.message_thread_id
            except Exception as e:
                await query.edit_message_text(
                    f"Не удалось создать топик: {e}\n\n"
                    "Убедись что Threaded Mode включён в @BotFather."
                )
                return
            session_store.set_project(thread_id, selected)
            await query.edit_message_text(
                f"✅ Топик <b>{folder_name}</b> создан!\n"
                f"Путь: <code>{selected}</code>\n\n"
                "Открой новый топик и начинай общаться с Claude.",
                parse_mode="HTML",
            )

        elif mode == "set":
            thread_id = context.user_data.get("set_thread_id")
            if not thread_id:
                await query.edit_message_text("Не удалось определить топик.")
                return
            session_store.set_project(thread_id, selected)
            folder_name = os.path.basename(selected)
            await query.edit_message_text(
                f"✅ Топик привязан к <b>{folder_name}</b>\n"
                f"Путь: <code>{selected}</code>",
                parse_mode="HTML",
            )


@authorized_only
async def handle_folder_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("awaiting_folder_name")
    if not mode:
        return False

    folder_name = update.message.text.strip()
    parent = context.user_data.get("browse_path", "")
    context.user_data.pop("awaiting_folder_name", None)

    if not folder_name or "/" in folder_name or folder_name.startswith("."):
        await update.message.reply_text(
            "Неверное имя папки. Без слешей и точек в начале. Попробуй /addproject заново."
        )
        return True

    new_path = os.path.join(parent, folder_name)

    if os.path.exists(new_path):
        await update.message.reply_text(
            f"Папка <code>{folder_name}</code> уже существует. Захожу в неё.",
            parse_mode="HTML",
        )
    else:
        try:
            os.makedirs(new_path, exist_ok=True)
        except OSError as e:
            await update.message.reply_text(f"Не удалось создать папку: {e}")
            return True

    context.user_data["browse_path"] = new_path
    kb = _build_keyboard(new_path, context, mode)
    await update.message.reply_text(
        f"Обзор: <code>{new_path}</code>", reply_markup=kb, parse_mode="HTML"
    )
    return True
