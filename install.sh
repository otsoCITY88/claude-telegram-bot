#!/bin/bash
set -e

echo "=== Claude Code Telegram Bot - Install ==="
echo

# Check Python 3
if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3.10+ first."
    exit 1
fi

PY_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "[OK] Python $PY_VERSION"

# Check Claude CLI
if command -v claude &>/dev/null; then
    echo "[OK] Claude CLI: $(which claude)"
else
    echo "[!!] Claude CLI not found in PATH."
    echo "     Install it: https://docs.anthropic.com/en/docs/claude-code/overview"
    echo "     Or set claude_cli_path in config.yaml"
fi

# Check ffmpeg (for voice messages)
if command -v ffmpeg &>/dev/null; then
    echo "[OK] ffmpeg found (voice messages will work)"
else
    echo "[!!] ffmpeg not found. Voice messages won't work."
    echo "     Install: sudo apt install ffmpeg"
fi

# Install Python dependencies
echo
echo "Installing dependencies..."
pip3 install -r requirements.txt --quiet 2>/dev/null || \
pip3 install -r requirements.txt --break-system-packages --quiet

echo
echo "[OK] Dependencies installed"

# Create config if needed
if [ ! -f config.yaml ]; then
    cp config.yaml.example config.yaml
    echo
    echo "=== config.yaml created ==="
    echo "Edit it now:"
    echo "  1. Set telegram_bot_token (get from @BotFather)"
    echo "  2. Set allowed_user_ids (get from @userinfobot)"
    echo "  3. Optionally set projects_root"
    echo
    echo "  nano config.yaml"
else
    echo "[OK] config.yaml already exists"
fi

echo
echo "=== To run ==="
echo "  python3 bot.py"
echo
echo "=== To run as a service ==="
echo "  1. Edit claude-bot.service (set User and paths)"
echo "  2. sudo cp claude-bot.service /etc/systemd/system/"
echo "  3. sudo systemctl daemon-reload"
echo "  4. sudo systemctl enable --now claude-bot"
echo
