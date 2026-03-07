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
# Собираем все ключи GEMINI_KEY_
ALL_KEYS = [os.getenv(k) for k in os.environ if k.startswith('GEMINI_KEY_')]
ALLOWED_CHATS = [-1002719419668, -1003371184723, -1002416957116]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Веб-сервер для Render ---
async def handle(request):
    return web.Response(text=f"Lal is unstoppable. Keys: {len(ALL_KEYS)}")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- Система подбора ключа ---
async def get_gemini_response(text):
    keys_pool = ALL_KEYS.copy()
    random.shuffle(keys_pool)
    
    for i, api_key in enumerate(keys_pool):
        try:
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel('gemini-1.5-flash') 
            
            prompt = (
                "Ты — Lal, тебе 16 лет. Ты мерзкий, грубый тип. Ты сидишь в чате и стебёшься над всеми. "
                "Твой стиль: сплошной текст без переносов строк. Ошибайся, капси от злости. "
                "ЗАПРЕЩЕНО: смайлы, тире, дефисы, жирный текст. Только ! . , ?. "
                "Ответь ровно в 7 предложений чистой агрессии на русском."
            )
            
            response = await model.generate_content_async(f"{prompt}\n\nПользователь: {text}")
            
            # Очистка от запрещенных знаков
            clean_text = response.text.replace("*", "").replace("-", "").replace("—", "").replace("_", "")
            return clean_text

        except (exceptions.ResourceExhausted, exceptions.InternalServerError, exceptions.ServiceUnavailable):
            continue 
        except Exception as e:
            logger.error(f"Ошибка на ключе: {str(e)[:50]}")
            continue

    return "даже все мои ключи сдохли от твоей рожи вали отсюда"

# --- Обработка сообщений ---
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

@dp.message(F.chat.id.in_(ALLOWED_CHATS))
async def handle_message(message: types.Message):
    if not message.text:
        return

    # Безопасная проверка упоминания (фикс AttributeError)
    bot_info = await bot.get_me()
    is_mentioned = False
    if message.entities:
        for e in message.entities:
            if e.type == "mention" and f"@{bot_info.username}" in message.text:
                is_mentioned = True
                break

    # Отвечаем ВСЕГДА, если есть триггер или тег
    if is_mentioned or "лал" in message.text.lower() or "lal" in message.text.lower():
        try:
            # Сразу показываем статус набора текста
            await bot.send_chat_action(message.chat.id, "typing")
            
            full_reply = await get_gemini_response(message.text)
            
            # Разбивка на 7 этапов для эффекта "живого" изменения
            sentences = [s.strip() for s in full_reply.replace('!', '.').replace('?', '.').split('.') if s.strip()]
            final_list = (sentences[:7] + ["че надо"] * 7)[:7]
            
            # Первое сообщение
            sent_msg = await message.reply(final_list[0])
            current_text = final_list[0]
            
            # Постепенное дописывание
            for i in range(1, 7):
                await asyncio.sleep(random.uniform(1.0, 3.0))
                current_text += " " + final_list[i]
                await sent_msg.edit_text(current_text)
                
        except Exception as e:
            logger.error(f"Ошибка в handle_message: {e}")

async def main():
    await start_server()
    logger.info(f"Lal Unstoppable запущен. Ключей: {len(ALL_KEYS)}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
