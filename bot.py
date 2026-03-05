import logging
import sys

from telegram import BotCommand
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from claude_bridge.session_store import SessionStore
from config import load_config
from handlers.chat import handle_message
from handlers.files import handle_file, handle_voice
from handlers.project import addproject_command, browse_callback, handle_folder_name, setproject_command
from handlers.session import (
    cancel_command,
    model_command,
    model_pick_callback,
    new_session,
    session_pick_callback,
    sessions_command,
    status_command,
    tools_toggle,
)
from handlers.start import start_command

logging.basicConfig(
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

BOT_COMMANDS = [
    BotCommand("start", "Приветствие и помощь"),
    BotCommand("addproject", "Выбрать папку и создать топик"),
    BotCommand("setproject", "Привязать топик к папке"),
    BotCommand("sessions", "Список сессий для продолжения"),
    BotCommand("new", "Новая сессия Claude"),
    BotCommand("cancel", "Прервать текущий запрос"),
    BotCommand("status", "Инфо о проекте и сессии"),
    BotCommand("model", "Выбрать модель Claude"),
    BotCommand("tools", "Вкл/выкл отображение тулов"),
]


async def post_init(application):
    await application.bot.set_my_commands(BOT_COMMANDS)
    log.info("Меню команд зарегистрировано (%d команд)", len(BOT_COMMANDS))


def main():
    config = load_config()

    if not config.telegram_bot_token:
        print("Укажи telegram_bot_token в config.yaml или переменную TELEGRAM_BOT_TOKEN")
        sys.exit(1)
    if not config.allowed_user_ids:
        print("Укажи allowed_user_ids в config.yaml или переменную ALLOWED_USER_IDS")
        sys.exit(1)

    session_store = SessionStore(config.sessions_file)

    app = (
        ApplicationBuilder()
        .token(config.telegram_bot_token)
        .post_init(post_init)
        .build()
    )

    app.bot_data["config"] = config
    app.bot_data["session_store"] = session_store
    app.bot_data["show_tools"] = True

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("addproject", addproject_command))
    app.add_handler(CommandHandler("setproject", setproject_command))
    app.add_handler(CommandHandler("new", new_session))
    app.add_handler(CommandHandler("cancel", cancel_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CommandHandler("sessions", sessions_command))
    app.add_handler(CommandHandler("model", model_command))
    app.add_handler(CommandHandler("tools", tools_toggle))

    app.add_handler(CallbackQueryHandler(browse_callback, pattern=r"^(br|sel|mkdir):"))
    app.add_handler(CallbackQueryHandler(session_pick_callback, pattern=r"^sess:"))
    app.add_handler(CallbackQueryHandler(model_pick_callback, pattern=r"^model:"))

    async def text_router(update, context):
        if context.user_data.get("awaiting_folder_name"):
            await handle_folder_name(update, context)
        else:
            await handle_message(update, context)

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_router))
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.ALL, handle_file))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))

    log.info("Бот запускается (user_ids=%s)", config.allowed_user_ids)
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
