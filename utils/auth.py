from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes


def authorized_only(func):
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        config = context.bot_data.get("config")
        user = update.effective_user
        if not user or not config or user.id not in config.allowed_user_ids:
            if update.effective_message:
                await update.effective_message.reply_text("Доступ запрещён.")
            elif update.callback_query:
                await update.callback_query.answer("Доступ запрещён.", show_alert=True)
            return
        return await func(update, context)

    return wrapper
