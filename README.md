# Claude Code Telegram Bot

[Русская версия](README_RU.md)

Telegram bot for working with [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/overview) right from your phone. Each project lives in a separate topic (thread) in your bot chat.

Claude Code performs real tasks: writes and edits code, runs commands, works with files in your projects.

## Features

- **Topics = projects** — each project in a separate thread, easy navigation
- **File manager** — choose a project folder via inline buttons, create new folders
- **Response streaming** — see what Claude is thinking and which tools it uses in real time
- **Intermediate messages** — text between tool calls is sent as separate messages
- **Model selection** — switch between Sonnet / Opus / Haiku per-project
- **Sessions** — resume any previous Claude Code session
- **Photos and files** — send a file in chat, Claude will read and analyze it
- **Voice messages** — speech-to-text (Google STT) → text is sent to Claude
- **Formatting** — Claude's Markdown and HTML are converted to Telegram HTML
- **Multi-user** — whitelist by Telegram user ID
- **i18n** — English and Russian interface
- **Auto-start** — systemd service with auto-restart

## Requirements

- Python 3.10+
- [Claude Code CLI](https://docs.anthropic.com/en/docs/claude-code/overview) (installed and authorized)
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- ffmpeg (optional, for voice messages)

## Quick Start

```bash
git clone https://github.com/otsoCITY88/claude-telegram-bot.git
cd claude-telegram-bot
bash install.sh
```

The installer does everything:
1. Checks dependencies (Python, Claude CLI, ffmpeg)
2. Installs Python packages
3. Asks for **Telegram Bot Token** (tells you where to get it)
4. Asks for **User ID** (tells you where to find it)
5. Asks for **projects folder**
6. Asks for **interface language** (English / Russian)
7. Offers to install a **systemd service** (auto-start)
8. Starts the bot

No manual file editing needed.

### Telegram Setup (before installation)

1. Open [@BotFather](https://t.me/BotFather) → `/newbot` → get your token
2. In BotFather: **Bot Settings → Topics in Private Chats → Enable**
3. Find your ID: message [@userinfobot](https://t.me/userinfobot)

## Bot Commands

| Command | Description |
|---|---|
| `/addproject` | Browse folders and create a project topic |
| `/setproject` | Bind an existing topic to a folder |
| `/sessions` | List sessions, resume any |
| `/new` | Start a new Claude session |
| `/cancel` | Cancel current request |
| `/model` | Choose model (Sonnet/Opus/Haiku) |
| `/status` | Project and session info |
| `/tools` | Toggle tool display |

## Configuration

Via `config.yaml` or environment variables:

| Parameter | Env | Default | Description |
|---|---|---|---|
| `telegram_bot_token` | `TELEGRAM_BOT_TOKEN` | — | Bot token |
| `allowed_user_ids` | `ALLOWED_USER_IDS` | — | List of Telegram user IDs |
| `claude_cli_path` | `CLAUDE_CLI_PATH` | auto | Path to Claude CLI |
| `projects_root` | `PROJECTS_ROOT` | `~/projects` | Root folder for projects |
| `permission_mode` | — | `bypassPermissions` | Claude permission mode |
| `max_budget_usd` | — | `5.0` | Budget limit per request |
| `max_depth` | — | `5` | File manager depth |
| `max_message_length` | — | `4000` | Max message length |
| `language` | — | `en` | Interface language (`en` / `ru`) |

## Auto-start (systemd)

```bash
# Edit the service file (User and paths)
nano claude-bot.service

# Install
sudo cp claude-bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now claude-bot

# Check
sudo systemctl status claude-bot
sudo journalctl -u claude-bot -f
```

## Project Structure

```
claude-telegram-bot/
├── bot.py                  # Entry point, handler registration
├── config.py               # Configuration (dataclass + yaml + env)
├── i18n.py                 # Internationalization (en/ru)
├── config.yaml.example     # Configuration template
├── requirements.txt        # Python dependencies
├── install.sh              # Installation script
├── claude-bot.service      # Systemd service
├── claude_bridge/
│   ├── runner.py           # Claude CLI launch, stream-json parsing
│   └── session_store.py    # topic→project mapping storage
├── handlers/
│   ├── start.py            # /start
│   ├── project.py          # /addproject, /setproject, file manager
│   ├── chat.py             # Message handling, response streaming
│   ├── session.py          # /sessions, /new, /model, /tools, /cancel
│   └── files.py            # Photos, documents, voice messages
└── utils/
    ├── auth.py             # Access check by user ID
    ├── formatting.py       # Markdown+HTML → Telegram HTML
    └── message_splitter.py # Long message splitting
```

## License

MIT
