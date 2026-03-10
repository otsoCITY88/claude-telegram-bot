import logging
import os
import subprocess
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from i18n import t
from utils.auth import authorized_only

log = logging.getLogger(__name__)

MAX_FILE_SIZE = 10 * 1024 * 1024

STT_LANGUAGES = {"en": "en-US", "ru": "ru-RU"}


@authorized_only
async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    thread_id = message.message_thread_id

    if not thread_id:
        await message.reply_text(t("send_in_topic"))
        return

    session_store = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await message.reply_text(t("not_bound"))
        return

    tg_file = None
    filename = None

    if message.photo:
        photo = message.photo[-1]
        if photo.file_size and photo.file_size > MAX_FILE_SIZE:
            await message.reply_text(t("file_too_big"))
            return
        tg_file = await photo.get_file()
        filename = f"photo_{tg_file.file_unique_id}.jpg"

    elif message.document:
        doc = message.document
        if doc.file_size and doc.file_size > MAX_FILE_SIZE:
            await message.reply_text(t("file_too_big"))
            return
        tg_file = await doc.get_file()
        filename = doc.file_name or f"file_{tg_file.file_unique_id}"

    if not tg_file or not filename:
        return

    save_path = os.path.join(info.project_path, filename)
    try:
        await tg_file.download_to_drive(save_path)
    except Exception as e:
        await message.reply_text(t("download_error", error=str(e)))
        return

    caption = message.caption or ""
    if caption:
        prompt = t("file_prompt_caption", filename=filename, path=save_path, caption=caption)
    else:
        prompt = t("file_prompt", filename=filename, path=save_path)

    await message.reply_text(
        f"📎 {t('file_saved', filename=filename)}", parse_mode="HTML"
    )

    from handlers.chat import send_to_claude
    await send_to_claude(message, prompt, context)


@authorized_only
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    thread_id = message.message_thread_id

    if not thread_id:
        await message.reply_text(t("voice_in_topic"))
        return

    session_store = context.bot_data["session_store"]
    info = session_store.get(thread_id)
    if not info:
        await message.reply_text(t("not_bound"))
        return

    voice = message.voice
    if not voice:
        return

    if voice.file_size and voice.file_size > MAX_FILE_SIZE:
        await message.reply_text(t("voice_too_big"))
        return

    status = await message.reply_text(f"🎤 {t('voice_recognizing')}")

    tg_file = await voice.get_file()
    config = context.bot_data["config"]
    stt_lang = STT_LANGUAGES.get(config.language, "en-US")

    try:
        text = await _transcribe_voice(tg_file, stt_lang)
    except Exception as e:
        log.exception("Voice transcription failed")
        await status.edit_text(t("voice_error", error=str(e)))
        return

    if not text or not text.strip():
        await status.edit_text(t("voice_empty"))
        return

    await status.edit_text(f"🎤 {t('voice_recognized', text=text)}", parse_mode="HTML")

    from handlers.chat import send_to_claude
    await send_to_claude(message, text, context)


async def _transcribe_voice(tg_file, language: str = "en-US") -> str:
    """Download voice .oga, convert to .wav, transcribe with SpeechRecognition."""
    import speech_recognition as sr

    with tempfile.TemporaryDirectory(prefix="voice_") as tmpdir:
        oga_path = os.path.join(tmpdir, "voice.oga")
        wav_path = os.path.join(tmpdir, "voice.wav")

        await tg_file.download_to_drive(oga_path)

        result = subprocess.run(
            ["ffmpeg", "-i", oga_path, "-ar", "16000", "-ac", "1", wav_path],
            capture_output=True,
            timeout=30,
        )
        if result.returncode != 0:
            raise RuntimeError(f"ffmpeg error: {result.stderr.decode()[:200]}")

        recognizer = sr.Recognizer()
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio, language=language)
        return text
