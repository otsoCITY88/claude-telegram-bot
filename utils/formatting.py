import re

_HTML_ESCAPE = str.maketrans({"&": "&amp;", "<": "&lt;", ">": "&gt;"})


def escape_html(text: str) -> str:
    return text.translate(_HTML_ESCAPE)


def claude_to_telegram_html(text: str) -> str:
    """Convert Claude's mixed markdown+HTML output to clean Telegram HTML.

    Claude often sends a mix of markdown and HTML tags.
    Strategy:
      1. Extract code blocks and inline code (escape contents)
      2. Extract existing HTML tags from Claude (preserve them)
      3. Escape all remaining &, <, >
      4. Convert markdown → HTML (headers, hr, bold, italic, lists, links)
      5. Restore all extracted elements
    """
    placeholders: dict[str, str] = {}
    counter = 0

    def _placeholder(content: str) -> str:
        nonlocal counter
        key = f"\x00PH{counter}\x00"
        counter += 1
        placeholders[key] = content
        return key

    # --- 1. Protect fenced code blocks ---
    def _code_block(m: re.Match) -> str:
        lang = m.group(1) or ""
        code = escape_html(m.group(2))
        if lang:
            return _placeholder(f'<pre><code class="language-{lang}">{code}</code></pre>')
        return _placeholder(f"<pre>{code}</pre>")

    text = re.sub(r"```(\w*)\n(.*?)```", _code_block, text, flags=re.DOTALL)

    # --- 2. Protect inline code ---
    text = re.sub(
        r"`([^`\n]+)`",
        lambda m: _placeholder(f"<code>{escape_html(m.group(1))}</code>"),
        text,
    )

    # --- 3. Protect existing HTML tags from Claude ---
    # Telegram supports: b, strong, i, em, u, ins, s, strike, del,
    #                     code, pre, a, span, tg-spoiler, blockquote
    _ALLOWED_TAGS = r"b|strong|i|em|u|ins|s|strike|del|code|pre|a|span|tg-spoiler|blockquote"
    text = re.sub(
        rf"<(/?)({_ALLOWED_TAGS})(\s[^>]*)?>",
        lambda m: _placeholder(m.group(0)),
        text,
    )

    # --- 4. Escape remaining & < > ---
    text = escape_html(text)

    # --- 5. Convert markdown to Telegram HTML ---

    # Headers: # / ## / ### etc → bold
    text = re.sub(r"^#{1,6}\s+(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Horizontal rules: --- or *** or ___ (3+)
    text = re.sub(r"^[-*_]{3,}\s*$", "⸻", text, flags=re.MULTILINE)

    # Bold: **text** or __text__
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"__(.+?)__", r"<b>\1</b>", text)

    # Italic: *text* or _text_ (not inside words)
    text = re.sub(r"(?<!\w)\*([^*]+?)\*(?!\w)", r"<i>\1</i>", text)
    text = re.sub(r"(?<!\w)_([^_]+?)_(?!\w)", r"<i>\1</i>", text)

    # Strikethrough: ~~text~~
    text = re.sub(r"~~(.+?)~~", r"<s>\1</s>", text)

    # Links: [text](url)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    # Unordered list items: - item or * item → • item
    text = re.sub(r"^[-*]\s+", "• ", text, flags=re.MULTILINE)

    # Ordered list items: 1. item → 1. item (just clean up, Telegram has no <ol>)
    # Already looks fine as-is

    # Blockquotes: > text (already escaped to &gt;)
    text = re.sub(r"^&gt;\s+(.+)$", r"<blockquote>\1</blockquote>", text, flags=re.MULTILINE)
    # Merge consecutive blockquotes
    text = re.sub(r"</blockquote>\n<blockquote>", "\n", text)

    # --- 6. Restore placeholders ---
    for key, value in placeholders.items():
        text = text.replace(key, value)

    return text
