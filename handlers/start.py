from telegram import Update
from telegram.ext import ContextTypes

from i18n import t
from utils.auth import authorized_only


@authorized_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(t("welcome"), parse_mode="HTML")
