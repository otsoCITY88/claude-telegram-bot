"""Internationalization — all user-facing strings in one place."""

STRINGS = {
    "en": {
        # bot.py — command descriptions
        "cmd_start": "Help and welcome",
        "cmd_addproject": "Browse folders and create topic",
        "cmd_setproject": "Bind current topic to a folder",
        "cmd_sessions": "List sessions to resume",
        "cmd_new": "Start new Claude session",
        "cmd_cancel": "Cancel current request",
        "cmd_status": "Project and session info",
        "cmd_model": "Choose Claude model",
        "cmd_tools": "Toggle tool display",

        # bot.py — startup errors
        "err_no_token": "Set telegram_bot_token in config.yaml or TELEGRAM_BOT_TOKEN env var",
        "err_no_users": "Set allowed_user_ids in config.yaml or ALLOWED_USER_IDS env var",

        # auth
        "access_denied": "Access denied.",

        # start
        "welcome": (
            "<b>Claude Code Bot</b>\n\n"
            "Commands:\n"
            "/addproject - Browse folders and create project topic\n"
            "/setproject - Bind current topic to a folder\n"
            "/sessions - List sessions, resume any\n"
            "/new - Start new Claude session\n"
            "/cancel - Cancel current request\n"
            "/model - Choose Claude model (sonnet/opus/haiku)\n"
            "/status - Project and session info\n"
            "/tools - Toggle tool display\n\n"
            "You can send photos and files — they'll be saved\n"
            "to the project folder and Claude will analyze them.\n\n"
            "Start with /addproject to connect your first project."
        ),

        # chat
        "use_topic": "Write in a project topic.\nUse /addproject to create one.",
        "topic_not_bound": "This topic is not bound to a project.\nUse /setproject here or /addproject for a new one.",
        "still_processing": "Still processing previous request. Wait.\nUse /cancel to abort.",
        "thinking": "Claude is thinking...",
        "working": "Working... ({elapsed}s)",
        "tools_label": "Tools:",
        "writing": "Writing response... ({elapsed}s)",
        "claude_working": "Claude is working... ({elapsed}s)",
        "tools_used": "Tools used ({count}):",
        "response_file": "(Response: {chars} chars — full text in the file above)",
        "chat_error": "Error: {error}",

        # session
        "use_in_topic": "Use this command inside a project topic.",
        "not_bound": "This topic is not bound to a project.",
        "new_session": "New session for <b>{folder}</b>.\nSend your first message.",
        "no_sessions": "No sessions found for this project.",
        "pick_session": "Pick a session to resume:",
        "sessions_title": "<b>Sessions — {folder}</b>{current}",
        "sessions_active": "\nActive: <code>{sid}...</code>",
        "session_not_found": "Session not found. Try /sessions again.",
        "cant_detect_topic": "Could not detect topic.",
        "session_resumed": "Resuming session <code>{sid}...</code>\nSend a message.",
        "no_model": "default",
        "none": "none",
        "model_current": "<b>Current model:</b> {model}\n\nChoose model for this project:",
        "model_reset_label": "Reset (default)",
        "model_reset_done": "Model reset — will use the default model.",
        "model_set": "Model: <b>{desc}</b>",
        "tools_on": "ON",
        "tools_off": "OFF",
        "tools_toggle": "Tool display: <b>{state}</b>",
        "nothing_running": "Nothing is running right now.",
        "cancelled": "Request cancelled.",

        # project
        "browse": "Browse: <code>{path}</code>",
        "folder_not_found": "Folder not found.",
        "enter_folder_name": "Enter new folder name:",
        "bad_folder_name": "Invalid folder name. No slashes or leading dots. Try /addproject again.",
        "folder_exists": "Folder <code>{name}</code> already exists. Entering it.",
        "folder_create_error": "Could not create folder: {error}",
        "topic_create_error": "Could not create topic: {error}\n\nMake sure Threaded Mode is enabled in @BotFather.",
        "project_created": "Project <b>{folder}</b>\nPath: <code>{path}</code>\n\nOpen the new topic and start chatting with Claude.",
        "project_bound": "Project <b>{folder}</b>\nPath: <code>{path}</code>",
        "use_in_topic_setproject": "Use this command inside a topic.",
        "new_folder_btn": "New folder",
        "back_btn": "Back",
        "select_btn": "Select this",

        # files
        "send_in_topic": "Send files in a project topic.\nUse /addproject to create one.",
        "file_too_big": "File is too big (max 10 MB).",
        "download_error": "Could not download file: {error}",
        "file_saved": "File saved: <code>{filename}</code>",
        "file_prompt": 'I added file "{filename}" to the project (full path: {path}). Read it with Read and analyze it.',
        "file_prompt_caption": 'I added file "{filename}" to the project (full path: {path}). {caption}',
        "voice_in_topic": "Send voice messages in a project topic.\nUse /addproject to create one.",
        "voice_too_big": "Voice message is too big (max 10 MB).",
        "voice_recognizing": "Recognizing voice...",
        "voice_error": "Could not recognize voice: {error}",
        "voice_empty": "Could not extract text from voice message.",
        "voice_recognized": "Recognized:\n<i>{text}</i>",

        # runner
        "request_cancelled": "Request cancelled.",
        "exit_code": "Exit code {code}",
        "claude_error": "Claude error:\n{error}",
        "process_timeout": "Claude worked for more than {minutes} min — process stopped.",

        # models
        "model_sonnet": "Sonnet — fast and cheap",
        "model_opus": "Opus — smartest",
        "model_haiku": "Haiku — fastest",

        # status
        "status_project": "<b>Project:</b> {folder}\n<b>Path:</b> <code>{path}</code>\n<b>Model:</b> {model}\n<b>Session:</b> {session}",
    },

    "ru": {
        "cmd_start": "Приветствие и помощь",
        "cmd_addproject": "Выбрать папку и создать топик",
        "cmd_setproject": "Привязать топик к папке",
        "cmd_sessions": "Список сессий для продолжения",
        "cmd_new": "Новая сессия Claude",
        "cmd_cancel": "Прервать текущий запрос",
        "cmd_status": "Инфо о проекте и сессии",
        "cmd_model": "Выбрать модель Claude",
        "cmd_tools": "Вкл/выкл отображение тулов",

        "err_no_token": "Укажи telegram_bot_token в config.yaml или переменную TELEGRAM_BOT_TOKEN",
        "err_no_users": "Укажи allowed_user_ids в config.yaml или переменную ALLOWED_USER_IDS",

        "access_denied": "Доступ запрещён.",

        "welcome": (
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
            "Начни с /addproject чтобы подключить первый проект."
        ),

        "use_topic": "Пиши в топике проекта.\nИспользуй /addproject чтобы создать.",
        "topic_not_bound": "Этот топик не привязан к проекту.\nИспользуй /setproject тут или /addproject для нового.",
        "still_processing": "Ещё обрабатываю предыдущий запрос. Подожди.\nИспользуй /cancel чтобы отменить.",
        "thinking": "Claude думает...",
        "working": "Работаю... ({elapsed}с)",
        "tools_label": "Тулы:",
        "writing": "Пишу ответ... ({elapsed}с)",
        "claude_working": "Claude работает... ({elapsed}с)",
        "tools_used": "Использовано тулов ({count}):",
        "response_file": "(Ответ: {chars} символов — полный текст в файле выше)",
        "chat_error": "Ошибка: {error}",

        "use_in_topic": "Используй эту команду внутри топика проекта.",
        "not_bound": "Этот топик не привязан к проекту.",
        "new_session": "Новая сессия для <b>{folder}</b>.\nПиши первое сообщение.",
        "no_sessions": "Сессий для этого проекта не найдено.",
        "pick_session": "Выбери сессию для продолжения:",
        "sessions_title": "<b>Сессии — {folder}</b>{current}",
        "sessions_active": "\nАктивная: <code>{sid}...</code>",
        "session_not_found": "Сессия не найдена. Попробуй /sessions заново.",
        "cant_detect_topic": "Не удалось определить топик.",
        "session_resumed": "Продолжаем сессию <code>{sid}...</code>\nПиши сообщение.",
        "no_model": "по умолчанию",
        "none": "нет",
        "model_current": "<b>Текущая модель:</b> {model}\n\nВыбери модель для этого проекта:",
        "model_reset_label": "Сбросить (по умолчанию)",
        "model_reset_done": "Модель сброшена — будет использоваться модель по умолчанию.",
        "model_set": "Модель: <b>{desc}</b>",
        "tools_on": "ВКЛ",
        "tools_off": "ВЫКЛ",
        "tools_toggle": "Отображение тулов: <b>{state}</b>",
        "nothing_running": "Сейчас ничего не выполняется.",
        "cancelled": "Запрос отменён.",

        "browse": "Обзор: <code>{path}</code>",
        "folder_not_found": "Папка не найдена.",
        "enter_folder_name": "Введи название новой папки:",
        "bad_folder_name": "Неверное имя папки. Без слешей и точек в начале. Попробуй /addproject заново.",
        "folder_exists": "Папка <code>{name}</code> уже существует. Захожу в неё.",
        "folder_create_error": "Не удалось создать папку: {error}",
        "topic_create_error": "Не удалось создать топик: {error}\n\nУбедись что Threaded Mode включён в @BotFather.",
        "project_created": "Проект <b>{folder}</b>\nПуть: <code>{path}</code>\n\nОткрой новый топик и начинай общаться с Claude.",
        "project_bound": "Проект <b>{folder}</b>\nПуть: <code>{path}</code>",
        "use_in_topic_setproject": "Используй эту команду внутри топика.",
        "new_folder_btn": "Новая папка",
        "back_btn": "Назад",
        "select_btn": "Выбрать эту",

        "send_in_topic": "Отправляй файлы в топике проекта.\nИспользуй /addproject чтобы создать.",
        "file_too_big": "Файл слишком большой (макс 10 МБ).",
        "download_error": "Не удалось скачать файл: {error}",
        "file_saved": "Файл сохранён: <code>{filename}</code>",
        "file_prompt": 'Я добавил файл "{filename}" в проект (полный путь: {path}). Прочитай его с помощью Read и проанализируй.',
        "file_prompt_caption": 'Я добавил файл "{filename}" в проект (полный путь: {path}). {caption}',
        "voice_in_topic": "Отправляй голосовые в топике проекта.\nИспользуй /addproject чтобы создать.",
        "voice_too_big": "Голосовое слишком большое (макс 10 МБ).",
        "voice_recognizing": "Распознаю голосовое...",
        "voice_error": "Не удалось распознать голосовое: {error}",
        "voice_empty": "Не удалось распознать текст из голосового.",
        "voice_recognized": "Распознано:\n<i>{text}</i>",

        "request_cancelled": "Запрос отменён.",
        "exit_code": "Код выхода {code}",
        "claude_error": "Ошибка Claude:\n{error}",
        "process_timeout": "Claude работал больше {minutes} мин — процесс остановлен.",

        "model_sonnet": "Sonnet — быстрый и дешёвый",
        "model_opus": "Opus — самый умный",
        "model_haiku": "Haiku — самый быстрый",

        "status_project": "<b>Проект:</b> {folder}\n<b>Путь:</b> <code>{path}</code>\n<b>Модель:</b> {model}\n<b>Сессия:</b> {session}",
    },
}

_lang = "en"


def set_language(lang: str):
    global _lang
    if lang in STRINGS:
        _lang = lang


def t(key: str, **kwargs) -> str:
    """Get translated string. Falls back to English, then returns the key."""
    text = STRINGS.get(_lang, {}).get(key) or STRINGS["en"].get(key) or key
    if kwargs:
        try:
            return text.format(**kwargs)
        except (KeyError, IndexError):
            return text
    return text
