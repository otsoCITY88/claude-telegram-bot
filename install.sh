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

step "1/6  Checking dependencies..."

if ! command -v python3 &>/dev/null; then
    fail "python3 not found. Install Python 3.10+"
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
        warn "Claude CLI not found."
        echo "     Install: https://docs.anthropic.com/en/docs/claude-code/overview"
        echo ""
        read -rp "  Path to claude (or Enter to skip): " CLAUDE_PATH
    fi
fi

HAS_FFMPEG=false
if command -v ffmpeg &>/dev/null; then
    ok "ffmpeg (voice messages will work)"
    HAS_FFMPEG=true
else
    warn "ffmpeg not found — voice messages won't work"
    echo "     Install: sudo apt install ffmpeg"
fi

# ── 2. Install Python dependencies ──────────────────────────

step "2/6  Installing Python dependencies..."

pip3 install -r requirements.txt --quiet 2>/dev/null || \
pip3 install -r requirements.txt --break-system-packages --quiet 2>/dev/null || \
fail "Could not install dependencies. Try: pip3 install -r requirements.txt"

ok "Dependencies installed"

# ── 3. Interactive config ────────────────────────────────────

step "3/6  Bot configuration..."

if [ -f config.yaml ]; then
    echo ""
    read -rp "  config.yaml already exists. Overwrite? [y/N]: " OVERWRITE
    if [[ ! "$OVERWRITE" =~ ^[Yy]$ ]]; then
        ok "Using existing config.yaml"
        SKIP_CONFIG=true
    fi
fi

if [ "${SKIP_CONFIG:-}" != "true" ]; then
    echo ""
    echo -e "  ${BOLD}Telegram Bot Token${NC}"
    echo "  Get one: open @BotFather in Telegram → /newbot"
    echo "  Also enable Threaded Mode: @BotFather → Bot Settings → Topics in Private Chats"
    echo ""
    while true; do
        read -rp "  Token: " BOT_TOKEN
        if [[ "$BOT_TOKEN" =~ ^[0-9]+:.+$ ]]; then
            break
        fi
        echo -e "  ${RED}Invalid format. Token looks like: 123456:ABC-DEF...${NC}"
    done

    echo ""
    echo -e "  ${BOLD}Your Telegram User ID${NC}"
    echo "  Find it: message @userinfobot in Telegram"
    echo ""
    while true; do
        read -rp "  User ID: " USER_ID
        if [[ "$USER_ID" =~ ^[0-9]+$ ]]; then
            break
        fi
        echo -e "  ${RED}User ID is a number. Try again.${NC}"
    done

    DEFAULT_ROOT="$HOME/projects"
    echo ""
    echo -e "  ${BOLD}Projects folder${NC}"
    read -rp "  Path [$DEFAULT_ROOT]: " PROJECTS_ROOT
    PROJECTS_ROOT="${PROJECTS_ROOT:-$DEFAULT_ROOT}"
    PROJECTS_ROOT="${PROJECTS_ROOT/#\~/$HOME}"

    if [ ! -d "$PROJECTS_ROOT" ]; then
        read -rp "  Folder does not exist. Create? [Y/n]: " CREATE_DIR
        if [[ ! "$CREATE_DIR" =~ ^[Nn]$ ]]; then
            mkdir -p "$PROJECTS_ROOT"
            ok "Created: $PROJECTS_ROOT"
        fi
    fi

    echo ""
    echo -e "  ${BOLD}Bot interface language${NC}"
    echo "  1) English (default)"
    echo "  2) Russian"
    echo ""
    read -rp "  Choice [1]: " LANG_CHOICE
    case "$LANG_CHOICE" in
        2) BOT_LANG="ru" ;;
        *) BOT_LANG="en" ;;
    esac
    ok "Language: $BOT_LANG"

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
language: "$BOT_LANG"
YAML

    if [ -n "$CLAUDE_PATH" ]; then
        echo "claude_cli_path: \"$CLAUDE_PATH\"" >> config.yaml
    fi

    ok "config.yaml created"
fi

# ── 4. Optional: systemd service ─────────────────────────────

step "4/6  Auto-start (systemd)..."
echo ""
read -rp "  Install as system service (auto-start)? [Y/n]: " INSTALL_SERVICE

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
        echo "  Proxy detected: $HTTP_PROXY"
        read -rp "  Add proxy to service? [Y/n]: " ADD_PROXY
        if [[ ! "$ADD_PROXY" =~ ^[Nn]$ ]]; then
            sed -i "/^Environment=HOME=/a Environment=HTTP_PROXY=$HTTP_PROXY\nEnvironment=HTTPS_PROXY=${HTTPS_PROXY:-$HTTP_PROXY}\nEnvironment=NO_PROXY=localhost,127.0.0.1,api.telegram.org" /tmp/claude-bot.service
        fi
    fi

    if sudo cp /tmp/claude-bot.service /etc/systemd/system/claude-bot.service && \
       sudo systemctl daemon-reload && \
       sudo systemctl enable claude-bot; then
        ok "Service installed"

        read -rp "  Start the bot now? [Y/n]: " START_NOW
        if [[ ! "$START_NOW" =~ ^[Nn]$ ]]; then
            sudo systemctl start claude-bot
            sleep 2
            if sudo systemctl is-active --quiet claude-bot; then
                ok "Bot is running!"
            else
                warn "Could not start. Check: sudo journalctl -u claude-bot -n 20"
            fi
        fi
    else
        warn "Could not install service (sudo required)"
        echo "     You can run manually: python3 bot.py"
    fi
    rm -f /tmp/claude-bot.service
else
    ok "Skipped"
fi

# ── 5. Done ──────────────────────────────────────────────────

step "5/6  Done!"

echo ""
echo -e "  ${GREEN}${BOLD}Bot is ready!${NC}"
echo ""
echo "  Commands:"
echo "    python3 bot.py                    — run manually"
echo "    sudo systemctl status claude-bot  — service status"
echo "    sudo journalctl -u claude-bot -f  — logs"
echo ""
echo "  In Telegram:"
echo "    1. Open your bot"
echo "    2. /start"
echo "    3. /addproject — choose a project"
echo "    4. Send messages in the project topic"
echo ""
