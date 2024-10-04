
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.utils import executor
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
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

# Функция для извлечения GPS-данных
def get_gps_info(exif_data):
    if not exif_data:
        return None
    
    gps_info = exif_data.get(34853)
    if gps_info:
        gps_data = {}
        for tag, value in gps_info.items():
            decoded = GPSTAGS.get(tag, tag)
            gps_data[decoded] = value

        return gps_data
    return None

# Конвертация GPS координат в удобный вид
def convert_to_degrees(value):
    d = float(value[0])
    m = float(value[1]) / 60.0
    s = float(value[2]) / 3600.0
    return d + m + s

# Описание каждого EXIF-тега
def describe_tag(tag, value):
    descriptions = {
        'DateTime': "📅 Время съёмки",
        'Make': "🏭 Производитель камеры",
        'Model': "📷 Модель устройства",
        'Software': "💾 Программное обеспечение",
        'ExifImageWidth': "↔️ Ширина изображения",
        'ExifImageHeight': "↕️ Высота изображения",
        'FNumber': "🔍 Диафрагма",
        'ExposureTime': "⏳ Выдержка",
        'ISOSpeedRatings': "🎛️ ISO (Чувствительность)",
        'FocalLength': "🔭 Фокусное расстояние",
        'GPSInfo': "📍 Местоположение (широта и долгота)",
    }

    if tag in descriptions:
        return f"<b>{descriptions[tag]}:</b> {value}"
    else:
        return f"<b>{tag}:</b> {value}"

# Функция для красивого форматирования метаданных
def format_metadata(metadata, gps_info=None):
    formatted_metadata = "<b>🔍 Найденные метаданные:</b>\n\n"
    for tag, value in metadata.items():
        formatted_metadata += describe_tag(tag, value) + "\n"
    
    # Обработка GPS данных
    if gps_info:
        lat = convert_to_degrees(gps_info['GPSLatitude'])
        lon = convert_to_degrees(gps_info['GPSLongitude'])
        formatted_metadata += f"<b>📍 Местоположение:</b> Широта: {lat}, Долгота: {lon}\n"
    
    return formatted_metadata

# Обработка метаданных изображения
def extract_metadata(file):
    image = Image.open(file)
    exif_data = image._getexif()
    if exif_data:
        metadata = {TAGS.get(tag): value for tag, value in exif_data.items()}
        gps_info = get_gps_info(exif_data)
        return metadata, gps_info
    return {}, None

# Обработка фото
@dp.message_handler(content_types=['photo', 'document'])
async def handle_docs_photo(message: types.Message):
    if await anti_spam(message):
        return

    file_info = await bot.get_file(message.document.file_id if message.document else message.photo[-1].file_id)
    file_path = file_info.file_path
    file = await bot.download_file(file_path)

    try:
        metadata, gps_info = extract_metadata(file)
        if metadata:
            formatted_metadata = format_metadata(metadata, gps_info)
            await message.reply(formatted_metadata, parse_mode=types.ParseMode.HTML)
            
            # Отправка местоположения, если есть GPS
            if gps_info:
                lat = convert_to_degrees(gps_info['GPSLatitude'])
                lon = convert_to_degrees(gps_info['GPSLongitude'])
                await bot.send_location(chat_id=message.chat.id, latitude=lat, longitude=lon)
        else:
            await message.reply("Извините, не удалось найти метаданные у этого файла.")
    except Exception as e:
        await message.reply(f"Произошла ошибка при обработке фото: {e}")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
