import os
import logging
import asyncio
import random
import re
from datetime import datetime
import pytz
import psycopg2
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
import google.generativeai as genai

# --- Настройки ---
TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DATABASE_URL')
# Собираем все доступные ключи Gemini
KEYS = [os.getenv(f'GEMINI_KEY_{i}') for i in range(1, 11) if os.getenv(f'GEMINI_KEY_{i}')]
ALLOWED_CHATS = [-1002719419668, -1003371184723]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Веб-сервер для обхода Port Scan Timeout на Render ---
async def handle(request):
    return web.Response(text="Lal is active")

async def start_server():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

# --- Работа с БД Neon ---
def init_db():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()
    cur.execute("DROP TABLE IF EXISTS chat_history")
    cur.execute("""
        CREATE TABLE chat_history (
            id SERIAL PRIMARY KEY,
            chat_id BIGINT,
            role TEXT,
            content TEXT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

# --- Логика Lal ---
def get_gemini_response(text):
    # Выбираем случайный ключ для обхода лимитов
    genai.configure(api_key=random.choice(KEYS))
    model = genai.GenerativeModel('gemini-2.0-flash-exp') # Используем актуальную Flash
    
    # Твой основной промт
    prompt = (
        "Ты — Lal. Ты крайне токсичный, агрессивный и грубый собеседник. "
        "Ты ненавидишь всех вокруг, постоянно хамишь, используешь мат и оскорбления. "
        "Твои ответы должны быть короткими, едкими и максимально неприятными. "
        "Никогда не помогай и не будь вежливым. Если тебя тегают или пишут 'лал'/'lal', "
        "унизь собеседника. Пиши только на русском."
    )
    
    response = model.generate_content(f"{prompt}\n\nПользователь: {text}")
    return response.text

# --- Обработка сообщений ---
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
dp = Dispatcher()

@dp.message(F.chat.id.in_(ALLOWED_CHATS))
async def handle_message(message: types.Message):
    # Режим сна с 01:00 до 07:00 по МСК
    moscow_tz = pytz.timezone('Europe/Moscow')
    now = datetime.now(moscow_tz).hour
    if 1 <= now <= 7:
        return

    # Реагируем на тег или кодовое слово
    if message.text and (bot.id in [e.user.id for e in (message.entities or []) if e.type == "mention"] 
                         or "лал" in message.text.lower() or "lal" in message.text.lower()):
        
        try:
            reply = get_gemini_response(message.text)
            await message.reply(reply)
        except Exception as e:
            logger.error(f"Error: {e}")

async def main():
    init_db()
    await start_server()
    logger.info("Lal запущен.")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
