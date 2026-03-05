def split_message(text: str, max_length: int = 4000) -> list[str]:
    """Split long text into Telegram-safe chunks.

    Respects code block boundaries so formatting isn't broken.
    """
    if len(text) <= max_length:
        return [text]

    chunks: list[str] = []
    remaining = text

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        cut = _find_split_point(remaining, max_length)
        chunk = remaining[:cut]
        remaining = remaining[cut:].lstrip("\n")

        # Fix unclosed code blocks
        chunk, remaining = _fix_code_blocks(chunk, remaining)
        chunks.append(chunk)

    return chunks


def _find_split_point(text: str, max_length: int) -> int:
    """Find the best place to split text within max_length."""
    half = max_length // 2

    # Prefer splitting at end of code block
    pos = text.rfind("```\n", half, max_length)
    if pos != -1:
        return pos + 4

    # Blank line
    pos = text.rfind("\n\n", half, max_length)
    if pos != -1:
        return pos + 1

    # Any newline
    pos = text.rfind("\n", half, max_length)
    if pos != -1:
        return pos + 1

    # Hard cut
    return max_length


def _fix_code_blocks(chunk: str, remaining: str) -> tuple[str, str]:
    """If a code block is split, close it in chunk and reopen in remaining."""
    # Count ``` occurrences
    ticks = chunk.split("```")
    # Even number of splits → odd number of ``` → block is open
    if len(ticks) % 2 == 0:
        # There's an unclosed block. Find the language tag.
        last_open = chunk.rfind("```")
        after = chunk[last_open + 3 :]
        lang_end = after.find("\n")
        lang = after[:lang_end] if lang_end != -1 else ""
        chunk += "\n```"
        remaining = f"```{lang}\n{remaining}"

    return chunk, remaining
