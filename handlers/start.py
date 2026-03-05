from telegram import Update
from telegram.ext import ContextTypes

from utils.auth import authorized_only


@authorized_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "<b>Claude Code Бот</b>\n\n"
        "Команды:\n"
        "/addproject - Выбрать папку и создать топик проекта\n"
        "/setproject - Привязать текущий топик к папке\n"
        "/sessions - Список сессий, продолжить любую\n"
        "/new - Начать новую сессию Claude\n"
        "/cancel - Прервать текущий запрос\n"
        "/model - Выбрать модель Claude (sonnet/opus/haiku)\n"
        "/status - Инфо о проекте и сессии\n"
        "/tools - Вкл/выкл отображение тулов\n\n"
        "Можно скидывать фото и файлы — они сохранятся\n"
        "в папку проекта и Claude их проанализирует.\n\n"
        "Начни с /addproject чтобы подключить первый проект.",
        parse_mode="HTML",
    )
