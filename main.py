import os
import logging
import asyncio
import random
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
import google.generativeai as genai

# --- Конфигурация ---
TOKEN = os.getenv('BOT_TOKEN')
KEYS = [os.getenv(f'GEMINI_KEY_{i}') for i in range(1, 11) if os.getenv(f'GEMINI_KEY_{i}')]
ALLOWED_CHATS = [-1002719419668, -1003371184723]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Веб-сервер для Render (Free Tier) ---
async def handle(request):
    return web.Response(text="Lal is here and he is pissed")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- Промпт "Живой Агрессор 16 лет" ---
async def get_gemini_response(text):
    genai.configure(api_key=random.choice(KEYS))
    model = genai.GenerativeModel('gemini-3-flash-preview')
    
    prompt = (
        "Ты — Lal, тебе 16 лет. Ты живой, грубый и мерзкий человек. "
        "Ты сидишь в чате с настоящими людьми и просто стебёшься над ними. "
        "Твой стиль: пиши сплошным текстом без переносов строк. "
        "Делай грамматические ошибки, иногда пиши КАПСОМ если тебя что-то бесит. "
        "ЗАПРЕЩЕНО использовать: смайлики, жирный текст (**), тире, дефисы и нижние подчеркивания. "
        "Разрешены только знаки: ! . , ?. Иногда специально пропускай запятые. "
        "Твой ответ должен состоять ровно из 7 предложений ненависти. Пиши на русском."
    )
    
    response = await model.generate_content_async(f"{prompt}\n\nПользователь: {text}")
    clean_text = response.text.replace("*", "").replace("-", "").replace("—", "").replace("_", "")
    return clean_text

# --- Обработка сообщений ---
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

@dp.message(F.chat.id.in_(ALLOWED_CHATS))
async def handle_message(message: types.Message):
    if not message.text:
        return

    # Безопасная проверка упоминания (Фикс ошибки NoneType)
    bot_info = await bot.get_me()
    is_mentioned = False
    if message.entities:
        for e in message.entities:
            if e.type == "mention" and f"@{bot_info.username}" in message.text:
                is_mentioned = True
                break

    if is_mentioned or "лал" in message.text.lower() or "lal" in message.text.lower():
        try:
            full_reply = await get_gemini_response(message.text)
            # Разбиваем на предложения (грубо, по точкам)
            sentences = [s.strip() for s in full_reply.replace('!', '.').replace('?', '.').split('.') if s.strip()]
            final_list = (sentences[:7] + ["че смотришь"] * 7)[:7]
            
            # Эффект живого набора текста (7 этапов редактирования)
            sent_msg = await message.reply(final_list[0])
            
            current_text = final_list[0]
            for i in range(1, 7):
                await asyncio.sleep(random.uniform(1.0, 3.0)) # Задержка 1-3 сек
                current_text += " " + final_list[i]
                await sent_msg.edit_text(current_text)
                
        except Exception as e:
            logger.error(f"Error: {e}")

async def main():
    await start_server()
    logger.info("Lal 16y.o. is live")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
