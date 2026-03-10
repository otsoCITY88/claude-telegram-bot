import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from i18n import t
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
        InlineKeyboardButton(f"📁+ {t('new_folder_btn')}", callback_data=f"mkdir:{mode}"),
        InlineKeyboardButton(f"✅ {t('select_btn')}", callback_data=f"sel:{mode}"),
    ]
    buttons.append(action_row)

    if os.path.normpath(path) != os.path.normpath(config.projects_root):
        parent = os.path.dirname(path)
        idx = str(len(path_map))
        path_map[idx] = parent
        buttons.append(
            [InlineKeyboardButton(f"⬆ {t('back_btn')}", callback_data=f"br:{mode}:{idx}")]
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
        t("browse", path=config.projects_root), reply_markup=kb, parse_mode="HTML"
    )


@authorized_only
async def setproject_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    thread_id = update.message.message_thread_id
    if not thread_id:
        await update.message.reply_text(t("use_in_topic_setproject"))
        return
    config = context.bot_data["config"]
    context.user_data["browse_path"] = config.projects_root
    context.user_data["path_map"] = {}
    context.user_data["set_thread_id"] = thread_id
    context.user_data.pop("awaiting_folder_name", None)
    kb = _build_keyboard(config.projects_root, context, mode="set")
    await update.message.reply_text(
        t("browse", path=config.projects_root), reply_markup=kb, parse_mode="HTML"
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
            await query.edit_message_text(t("folder_not_found"))
            return
        context.user_data["browse_path"] = new_path
        context.user_data.pop("awaiting_folder_name", None)
        kb = _build_keyboard(new_path, context, mode)
        await query.edit_message_text(
            t("browse", path=new_path), reply_markup=kb, parse_mode="HTML"
        )

    elif action == "mkdir":
        current = context.user_data.get("browse_path", "")
        context.user_data["awaiting_folder_name"] = mode
        await query.edit_message_text(
            f"📁 <code>{current}</code>\n\n{t('enter_folder_name')}",
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
                await query.edit_message_text(t("topic_create_error", error=str(e)))
                return
            session_store.set_project(thread_id, selected)
            await query.edit_message_text(
                f"✅ {t('project_created', folder=folder_name, path=selected)}",
                parse_mode="HTML",
            )

        elif mode == "set":
            thread_id = context.user_data.get("set_thread_id")
            if not thread_id:
                await query.edit_message_text(t("cant_detect_topic"))
                return
            session_store.set_project(thread_id, selected)
            folder_name = os.path.basename(selected)
            await query.edit_message_text(
                f"✅ {t('project_bound', folder=folder_name, path=selected)}",
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
        await update.message.reply_text(t("bad_folder_name"))
        return True

    new_path = os.path.join(parent, folder_name)

    if os.path.exists(new_path):
        await update.message.reply_text(
            t("folder_exists", name=folder_name), parse_mode="HTML"
        )
    else:
        try:
            os.makedirs(new_path, exist_ok=True)
        except OSError as e:
            await update.message.reply_text(t("folder_create_error", error=str(e)))
            return True

    context.user_data["browse_path"] = new_path
    kb = _build_keyboard(new_path, context, mode)
    await update.message.reply_text(
        t("browse", path=new_path), reply_markup=kb, parse_mode="HTML"
    )
    return True
