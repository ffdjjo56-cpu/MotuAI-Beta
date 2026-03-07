import os
import logging
import asyncio
import random
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
import google.generativeai as genai
from google.api_core import exceptions

# --- Конфигурация ---
TOKEN = os.getenv('BOT_TOKEN')
# Автоматический сбор всех ключей GEMINI_KEY_ из переменных окружения Render
ALL_KEYS = [os.getenv(k) for k in os.environ if k.startswith('GEMINI_KEY_')]
# Список разрешенных чатов
ALLOWED_CHATS = [-1002719419668, -1003371184723, -1002416957116]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Веб-сервер для поддержания жизни на Render ---
async def handle(request):
    return web.Response(text=f"Lal is running. Keys detected: {len(ALL_KEYS)}")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- Система мгновенного подбора рабочего ключа ---
async def get_gemini_response(text):
    keys_pool = ALL_KEYS.copy()
    random.shuffle(keys_pool)
    
    for i, api_key in enumerate(keys_pool):
        try:
            genai.configure(api_key=api_key)
            # Используем gemini-1.5-flash для самой высокой скорости ответа
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            prompt = (
                "Ты — Lal, тебе 16 лет. Ты живой, грубый и мерзкий человек. "
                "Ты сидишь в чате с настоящими людьми и просто стебёшься над ними. "
                "Твой стиль: пиши сплошным текстом без переносов строк. "
                "Делай грамматические ошибки, иногда пиши КАПСОМ от злости. "
                "ЗАПРЕЩЕНО использовать: смайлики, жирный текст (**), тире, дефисы, нижние подчеркивания. "
                "Разрешены только знаки: ! . , ?. Иногда специально пропускай запятые. "
                "Твой ответ должен состоять ровно из 7 предложений ненависти. Пиши на русском."
            )
            
            response = await model.generate_content_async(f"{prompt}\n\nПользователь: {text}")
            
            # Жесткая очистка текста от лишних символов форматирования
            clean_text = response.text.replace("*", "").replace("-", "").replace("—", "").replace("_", "")
            return clean_text

        except (exceptions.ResourceExhausted, exceptions.InternalServerError, exceptions.ServiceUnavailable):
            # Если ключ исчерпан или сбой сервера Google — берем следующий
            continue 
        except Exception as e:
            logger.error(f"Ошибка на ключе {i}: {str(e)[:50]}")
            continue

    return "слыш у меня даже все 35 ключей сдохли от твоей рожи вали отсюда"

# --- Основная логика бота ---
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

@dp.message(F.chat.id.in_(ALLOWED_CHATS))
async def handle_message(message: types.Message):
    if not message.text:
        return

    # Безопасная проверка упоминания (исправляет падение бота при пустых сущностях)
    bot_info = await bot.get_me()
    is_mentioned = False
    if message.entities:
        for e in message.entities:
            if e.type == "mention" and f"@{bot_info.username}" in message.text:
                is_mentioned = True
                break

    # Мгновенная реакция на триггеры без задержек и шансов
    if is_mentioned or "лал" in message.text.lower() or "lal" in message.text.lower():
        try:
            # Визуальный индикатор набора текста
            await bot.send_chat_action(message.chat.id, "typing")
            
            # Получаем ответ через систему ротации ключей
            full_reply = await get_gemini_response(message.text)
            
            # Отправляем весь текст сразу одним сообщением
            await message.reply(full_reply)
                
        except Exception as e:
            logger.error(f"Ошибка при отправке: {e}")

async def main():
    # Запуск сервера и бота
    await start_server()
    logger.info(f"Lal Fast-Mode запущен. Ключей в обойме: {len(ALL_KEYS)}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
