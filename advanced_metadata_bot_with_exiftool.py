
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
import exiftool
import time

API_TOKEN = '7964169165:AAEKm-k603knI-iHrVso6ITXR094Nx8YJC0'

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())

user_requests = {}

# Антиспам-система с уведомлением и блокировкой всех запросов
async def anti_spam(message: types.Message):
    user_id = message.from_user.id
    current_time = time.time()

    if user_id in user_requests:
        request_times = user_requests[user_id]
        request_times = [req for req in request_times if current_time - req < 2]
        if len(request_times) >= 5:
            await message.answer("Наша анти-спам система обнаружила подозрительное поведение. Пожалуйста, не спамьте⛔️\nP.S. Вы были временно заблокированы в боте⌛️")
            await asyncio.sleep(20)  # Игнорирование сообщений на 20 секунд
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

    await message.answer("Добро пожаловать в бота для просмотра метаданных медиафайлов! Отправьте фото, чтобы увидеть всю доступную информацию, включая EXIF📸.\n\nСоздатель👑: @OS7NT")

# Форматирование метаданных
def format_metadata(metadata):
    formatted_metadata = "<b>🔍 Найденные метаданные:</b>\n\n"
    for tag, value in metadata.items():
        formatted_metadata += f"<b>{tag}:</b> {value}\n"
    
    return formatted_metadata

# Обработка метаданных изображения с использованием ExifTool
def extract_metadata(file):
    with exiftool.ExifTool() as et:
        metadata = et.get_metadata(file)
    return metadata

# Обработка фото
@dp.message_handler(content_types=['photo', 'document'])
async def handle_docs_photo(message: types.Message):
    if await anti_spam(message):
        return

    file_info = await bot.get_file(message.document.file_id if message.document else message.photo[-1].file_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)

    try:
        metadata = extract_metadata(file.name)
        if metadata:
            formatted_metadata = format_metadata(metadata)
            await message.reply(formatted_metadata, parse_mode=types.ParseMode.HTML)
            
            # Проверка на GPS данные и отправка местоположения
            if 'Composite:GPSLatitude' in metadata and 'Composite:GPSLongitude' in metadata:
                lat = metadata['Composite:GPSLatitude']
                lon = metadata['Composite:GPSLongitude']
                await bot.send_location(chat_id=message.chat.id, latitude=lat, longitude=lon)
        else:
            await message.reply("Извините, не удалось найти метаданные у этого файла.")
    except Exception as e:
        await message.reply(f"Произошла ошибка при обработке фото: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
