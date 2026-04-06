import os
import logging
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from yandex_music import Client

# Включаем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Получаем токены из переменных окружения ---
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
YANDEX_TOKEN = os.environ.get("YANDEX_MUSIC_TOKEN")

if not TELEGRAM_TOKEN or not YANDEX_TOKEN:
    logger.error("❌ Ошибка: не найдены переменные окружения TELEGRAM_BOT_TOKEN или YANDEX_MUSIC_TOKEN")
    exit(1)


def extract_track_id(url: str) -> str:
    """Извлекает ID трека из URL Яндекс.Музыки"""
    # Ищем паттерн /track/ЧИСЛО
    match = re.search(r'/track/(\d+)', url)
    if match:
        return match.group(1)
    return None


# --- Команда /start ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Привет! Я бот для Яндекс Музыки!\n\n"
        "Отправь мне ссылку на трек, и я пришлю его название, исполнителя и длительность.\n"
        "Пример: https://music.yandex.ru/album/35390921/track/136101918"
    )


# --- Обработка ссылок ---
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    logger.info(f"Получен URL: {url}")

    # Отправляем уведомление о наборе текста
    await update.message.chat.send_action(action="typing")

    # Извлекаем ID трека из URL
    track_id = extract_track_id(url)
    if not track_id:
        await update.message.reply_text(
            "❌ Не удалось найти ID трека в ссылке.\n"
            "Убедитесь, что ссылка содержит /track/число"
        )
        return

    try:
        # Создаём клиент Яндекс.Музыки
        client = Client(YANDEX_TOKEN).init()

        # Используем метод tracks() (с s на конце), который принимает список ID
        # Метод возвращает список треков
        tracks = client.tracks([track_id])

        if not tracks:
            await update.message.reply_text("❌ Трек не найден")
            return

        track = tracks[0]  # Берем первый (и единственный) трек

        # Получаем данные
        title = track.title
        artists = ", ".join([artist.name for artist in track.artists])
        duration_ms = track.duration_ms
        duration_sec = duration_ms // 1000
        minutes = duration_sec // 60
        seconds = duration_sec % 60

        # Формируем ответ
        response = (
            f"🎉 <b>Информация о треке</b> 🎉\n\n"
            f"🎵 <b>Название:</b> {title}\n"
            f"👨‍🎤 <b>Исполнитель:</b> {artists}\n"
            f"⏱️ <b>Длительность:</b> {minutes}:{seconds:02d}"
        )

        await update.message.reply_text(response, parse_mode="HTML")
        logger.info(f"✅ Успешно: {title} - {artists}")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        await update.message.reply_text(
            "❌ Не удалось найти информацию по этой ссылке.\n"
            "Пожалуйста, убедитесь, что ссылка ведёт именно на трек в Яндекс Музыке"
        )


# --- Запуск бота ---
def main():
    # Создаём приложение
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    # Добавляем обработчики
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Бот запущен и готов к работе!")
    app.run_polling(allowed_updates=[])


if __name__ == "__main__":
    main()
