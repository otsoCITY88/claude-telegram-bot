# Claude Code Telegram Bot

Telegram-бот для работы с [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/overview) прямо с телефона. Каждый проект — отдельный топик (тред) в чате с ботом.

Claude Code выполняет реальные задачи: пишет и редактирует код, запускает команды, работает с файлами в ваших проектах.

## Возможности

- **Топики = проекты** — каждый проект в отдельном треде, удобная навигация
- **Файловый менеджер** — выбор проекта через inline-кнопки, создание новых папок
- **Стриминг ответов** — видно что Claude думает и какие тулы использует в реальном времени
- **Промежуточные сообщения** — текст между вызовами тулов отправляется как отдельные сообщения
- **Выбор модели** — переключение между Sonnet / Opus / Haiku per-project
- **Сессии** — продолжение любой предыдущей сессии Claude Code
- **Фото и файлы** — отправь файл в чат, Claude его прочитает и проанализирует
- **Голосовые** — speech-to-text (Google STT) → текст отправляется в Claude
- **Форматирование** — Markdown и HTML Claude конвертируются в Telegram HTML
- **Мульти-юзер** — whitelist по Telegram user ID
- **Автозапуск** — systemd сервис с автоперезапуском

## Требования

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/overview) (установлен и авторизован)
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- ffmpeg (опционально, для голосовых сообщений)

## Быстрый старт

```bash
git clone https://github.com/otsoCITY88/claude-telegram-bot.git
cd claude-telegram-bot
bash install.sh
```

Скрипт установит зависимости и создаст `config.yaml`. Отредактируйте его:

```bash
nano config.yaml
```

Обязательные поля:
- `telegram_bot_token` — токен от @BotFather
- `allowed_user_ids` — ваш Telegram ID (узнать: [@userinfobot](https://t.me/userinfobot))

Запуск:

```bash
python3 bot.py
```

## Настройка бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather)
2. Включите **Threaded Mode** для бота (нужно для топиков в личном чате)
3. Напишите боту `/start`
4. Создайте первый проект: `/addproject`

## Команды бота

| Команда | Описание |
|---|---|
| `/addproject` | Выбрать папку и создать топик проекта |
| `/setproject` | Привязать существующий топик к папке |
| `/sessions` | Список сессий, продолжить любую |
| `/new` | Начать новую сессию Claude |
| `/cancel` | Прервать текущий запрос |
| `/model` | Выбрать модель (Sonnet/Opus/Haiku) |
| `/status` | Инфо о проекте и сессии |
| `/tools` | Вкл/выкл отображение тулов |

## Конфигурация

Через `config.yaml` или переменные окружения:

| Параметр | Env | По умолчанию | Описание |
|---|---|---|---|
| `telegram_bot_token` | `TELEGRAM_BOT_TOKEN` | — | Токен бота |
| `allowed_user_ids` | `ALLOWED_USER_IDS` | — | Список Telegram user ID |
| `claude_cli_path` | `CLAUDE_CLI_PATH` | auto | Путь к Claude CLI |
| `projects_root` | `PROJECTS_ROOT` | `~/projects` | Корневая папка проектов |
| `permission_mode` | — | `bypassPermissions` | Режим разрешений Claude |
| `max_budget_usd` | — | `5.0` | Лимит бюджета на запрос |
| `max_depth` | — | `5` | Глубина файлового менеджера |
| `max_message_length` | — | `4000` | Макс. длина сообщения |

## Автозапуск (systemd)

```bash
# Отредактируйте сервис (User и пути)
nano claude-bot.service

# Установите
sudo cp claude-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now claude-bot

# Проверьте
sudo systemctl status claude-bot
sudo journalctl -u claude-bot -f
```

## Структура проекта

```
claude-telegram-bot/
├── bot.py                  # Точка входа, регистрация хендлеров
├── config.py               # Конфигурация (dataclass + yaml + env)
├── config.yaml.example     # Шаблон конфигурации
├── requirements.txt        # Python зависимости
├── install.sh              # Скрипт установки
├── claude-bot.service      # Systemd сервис
├── claude_bridge/
│   ├── runner.py           # Запуск Claude CLI, парсинг stream-json
│   └── session_store.py    # Хранение topic→project маппинга
├── handlers/
│   ├── start.py            # /start
│   ├── project.py          # /addproject, /setproject, файловый менеджер
│   ├── chat.py             # Обработка сообщений, стриминг ответов
│   ├── session.py          # /sessions, /new, /model, /tools, /cancel
│   └── files.py            # Фото, документы, голосовые
└── utils/
    ├── auth.py             # Проверка доступа по user ID
    ├── formatting.py       # Markdown+HTML → Telegram HTML
    └── message_splitter.py # Разбивка длинных сообщений
```

## Лицензия

MIT
