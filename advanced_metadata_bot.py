
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from aiogram.utils.exceptions import Throttled
from PIL import Image
from PIL.ExifTags import TAGS
import os
import time

API_TOKEN = '7964169165:AAEKm-k603knI-iHrVso6ITXR094Nx8YJC0'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

user_requests = {}

# Антиспам-система
async def anti_spam(message: types.Message):
    user_id = message.from_user.id
    current_time = time.time()

    if user_id in user_requests:
        request_times = user_requests[user_id]
        request_times = [req for req in request_times if current_time - req < 2]
        if len(request_times) >= 5:
            await message.answer("Наша анти-спам система обнаружила подозрительное поведение. Пожалуйста, не спамьте⛔️\nP.S. Вы были временно заблокированы в боте⌛️")
            await asyncio.sleep(20)  # Блокировка на 20 секунд
            return True
        else:
            user_requests[user_id].append(current_time)
    else:
        user_requests[user_id] = [current_time]

    return False

# Команда /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if await anti_spam(message):
        return

    await message.answer("Добро пожаловать в бота для просмотра метаданных медиафайлов, пожалуйста, отправьте фото в любом формате для начала обработки🤫\n\nСоздатель👑: @OS7NT")

# Функция для красивого форматирования метаданных
def format_metadata(metadata):
    formatted_metadata = "<b>🔍 Найденные метаданные:</b>\n\n"
    for key, value in metadata.items():
        formatted_metadata += f"<b>{key}:</b> {value}\n"
    return formatted_metadata

# Обработка метаданных изображения
def extract_metadata(file):
    image = Image.open(file)
    exif_data = image._getexif()
    if exif_data:
        metadata = {TAGS.get(tag): value for tag, value in exif_data.items()}
        return metadata
    return {}

# Обработка фото
@dp.message_handler(content_types=['photo', 'document'])
async def handle_docs_photo(message: types.Message):
    if await anti_spam(message):
        return

    file_info = await bot.get_file(message.document.file_id if message.document else message.photo[-1].file_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)

    try:
        metadata = extract_metadata(file)
        if metadata:
            formatted_metadata = format_metadata(metadata)
            await message.reply(formatted_metadata, parse_mode=types.ParseMode.HTML)
        else:
            await message.reply("Извините, не удалось найти метаданные у этого файла.")
    except Exception as e:
        await message.reply(f"Произошла ошибка при обработке фото: {e}")

# Антиспам для текста (в данном случае блокируем простые сообщения)
@dp.message_handler(lambda message: not message.text.startswith('/'))
async def handle_text(message: types.Message):
    if await anti_spam(message):
        return

    await message.reply("Пожалуйста, отправьте фото для анализа метаданных.")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
