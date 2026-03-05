#!/bin/bash
set -e

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}[OK]${NC} $1"; }
warn() { echo -e "  ${YELLOW}[!!]${NC} $1"; }
fail() { echo -e "  ${RED}[ERROR]${NC} $1"; exit 1; }
step() { echo -e "\n${BOLD}$1${NC}"; }

echo -e "${BOLD}"
echo "╔══════════════════════════════════════╗"
echo "║  Claude Code Telegram Bot - Setup    ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── 1. Check prerequisites ──────────────────────────────────

step "1/5  Проверка зависимостей..."

if ! command -v python3 &>/dev/null; then
    fail "python3 не найден. Установи Python 3.10+"
fi
PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
ok "Python $PY_VER"

CLAUDE_PATH=""
if command -v claude &>/dev/null; then
    CLAUDE_PATH=$(which claude)
    ok "Claude CLI: $CLAUDE_PATH"
else
    for p in "$HOME/.local/bin/claude" "$HOME/.claude/local/claude" "/usr/local/bin/claude"; do
        if [ -f "$p" ]; then
            CLAUDE_PATH="$p"
            break
        fi
    done
    if [ -n "$CLAUDE_PATH" ]; then
        ok "Claude CLI: $CLAUDE_PATH"
    else
        warn "Claude CLI не найден."
        echo "     Установи: https://docs.anthropic.com/en/docs/claude-code/overview"
        echo ""
        read -rp "  Путь к claude (или Enter чтобы пропустить): " CLAUDE_PATH
    fi
fi

HAS_FFMPEG=false
if command -v ffmpeg &>/dev/null; then
    ok "ffmpeg (голосовые сообщения будут работать)"
    HAS_FFMPEG=true
else
    warn "ffmpeg не найден — голосовые сообщения не будут работать"
    echo "     Установить: sudo apt install ffmpeg"
fi

# ── 2. Install Python dependencies ──────────────────────────

step "2/5  Установка Python-зависимостей..."

pip3 install -r requirements.txt --quiet 2>/dev/null || \
pip3 install -r requirements.txt --break-system-packages --quiet 2>/dev/null || \
fail "Не удалось установить зависимости. Попробуй: pip3 install -r requirements.txt"

ok "Зависимости установлены"

# ── 3. Interactive config ────────────────────────────────────

step "3/5  Настройка бота..."

if [ -f config.yaml ]; then
    echo ""
    read -rp "  config.yaml уже существует. Перезаписать? [y/N]: " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        ok "Используем существующий config.yaml"
        SKIP_CONFIG=true
    fi
fi

if [ "${SKIP_CONFIG:-}" != "true" ]; then
    echo ""
    echo -e "  ${BOLD}Telegram Bot Token${NC}"
    echo "  Получить: открой @BotFather в Telegram → /newbot"
    echo "  Также включи Threaded Mode: @BotFather → Bot Settings → Topics in Private Chats"
    echo ""
    while true; do
        read -rp "  Токен: " BOT_TOKEN
        if [[ "$BOT_TOKEN" =~ ^[0-9]+:.+$ ]]; then
            break
        fi
        echo -e "  ${RED}Неверный формат. Токен выглядит как: 123456:ABC-DEF...${NC}"
    done

    echo ""
    echo -e "  ${BOLD}Твой Telegram User ID${NC}"
    echo "  Узнать: напиши @userinfobot в Telegram"
    echo ""
    while true; do
        read -rp "  User ID: " USER_ID
        if [[ "$USER_ID" =~ ^[0-9]+$ ]]; then
            break
        fi
        echo -e "  ${RED}User ID — это число. Попробуй ещё раз.${NC}"
    done

    DEFAULT_ROOT="$HOME/projects"
    echo ""
    echo -e "  ${BOLD}Папка с проектами${NC}"
    read -rp "  Путь [$DEFAULT_ROOT]: " PROJECTS_ROOT
    PROJECTS_ROOT="${PROJECTS_ROOT:-$DEFAULT_ROOT}"
    PROJECTS_ROOT="${PROJECTS_ROOT/#\~/$HOME}"

    if [ ! -d "$PROJECTS_ROOT" ]; then
        read -rp "  Папка не существует. Создать? [Y/n]: " CREATE_DIR
        if [[ ! "$CREATE_DIR" =~ ^[Nn]$ ]]; then
            mkdir -p "$PROJECTS_ROOT"
            ok "Создана: $PROJECTS_ROOT"
        fi
    fi

    # Write config
    cat > config.yaml << YAML
telegram_bot_token: "$BOT_TOKEN"

allowed_user_ids:
  - $USER_ID

permission_mode: "bypassPermissions"
allowed_tools:
  - Bash
  - Read
  - Write
  - Edit
  - Glob
  - Grep
max_budget_usd: 5.0

projects_root: "$PROJECTS_ROOT"
max_depth: 5
max_message_length: 4000
YAML

    if [ -n "$CLAUDE_PATH" ]; then
        echo "claude_cli_path: \"$CLAUDE_PATH\"" >> config.yaml
    fi

    ok "config.yaml создан"
fi

# ── 4. Optional: systemd service ─────────────────────────────

step "4/5  Автозапуск (systemd)..."
echo ""
read -rp "  Установить как системный сервис (автозапуск)? [Y/n]: " INSTALL_SERVICE

if [[ ! "$INSTALL_SERVICE" =~ ^[Nn]$ ]]; then
    BOT_DIR="$(pwd)"
    BOT_USER="$(whoami)"

    cat > /tmp/claude-bot.service << SERVICE
[Unit]
Description=Claude Code Telegram Bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=$BOT_USER
WorkingDirectory=$BOT_DIR
ExecStart=/usr/bin/python3 $BOT_DIR/bot.py
Restart=always
RestartSec=5
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=$HOME

StandardOutput=journal
StandardError=journal
SyslogIdentifier=claude-bot

[Install]
WantedBy=multi-user.target
SERVICE

    # Check if proxy is set
    if [ -n "$HTTP_PROXY" ]; then
        echo "  Обнаружен прокси: $HTTP_PROXY"
        read -rp "  Добавить прокси в сервис? [Y/n]: " ADD_PROXY
        if [[ ! "$ADD_PROXY" =~ ^[Nn]$ ]]; then
            sed -i "/^Environment=HOME=/a Environment=HTTP_PROXY=$HTTP_PROXY\nEnvironment=HTTPS_PROXY=${HTTPS_PROXY:-$HTTP_PROXY}\nEnvironment=NO_PROXY=localhost,127.0.0.1,api.telegram.org" /tmp/claude-bot.service
        fi
    fi

    if sudo cp /tmp/claude-bot.service /etc/systemd/system/claude-bot.service && \
       sudo systemctl daemon-reload && \
       sudo systemctl enable claude-bot; then
        ok "Сервис установлен"

        read -rp "  Запустить бота прямо сейчас? [Y/n]: " START_NOW
        if [[ ! "$START_NOW" =~ ^[Nn]$ ]]; then
            sudo systemctl start claude-bot
            sleep 2
            if sudo systemctl is-active --quiet claude-bot; then
                ok "Бот запущен!"
            else
                warn "Не удалось запустить. Проверь: sudo journalctl -u claude-bot -n 20"
            fi
        fi
    else
        warn "Не удалось установить сервис (нужен sudo)"
        echo "     Можно запустить вручную: python3 bot.py"
    fi
    rm -f /tmp/claude-bot.service
else
    ok "Пропущено"
fi

# ── 5. Done ──────────────────────────────────────────────────

step "5/5  Готово!"

echo ""
echo -e "  ${GREEN}${BOLD}Бот готов к работе!${NC}"
echo ""
echo "  Команды:"
echo "    python3 bot.py              — запуск вручную"
echo "    sudo systemctl status claude-bot — статус сервиса"
echo "    sudo journalctl -u claude-bot -f — логи"
echo ""
echo "  В Telegram:"
echo "    1. Открой бота"
echo "    2. /start"
echo "    3. /addproject — выбери проект"
echo "    4. Пиши сообщения в топике проекта"
echo ""
