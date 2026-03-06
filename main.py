import os
import logging
import asyncio
import time
import random
import re
import aiohttp
import psycopg2 
import pytz
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.chat_action import ChatActionSender
from aiohttp import web
import google.generativeai as genai


API_TOKEN = os.getenv('BOT_TOKEN')
DB_URL = os.getenv('DATABASE_URL') 
CHAT_KEYS = sorted([os.getenv(k) for k in os.environ if k.startswith('GEMINI_KEY')])
RENDER_URL = os.getenv('RENDER_EXTERNAL_URL')

ALLOWED_CHATS = [-1002719419668, -1003371184723] 
bot_id = None 

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(name)


def init_db():
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("DROP TABLE IF EXISTS chat_history") 
        cur.execute("""
            CREATE TABLE chat_history (
                id SERIAL PRIMARY KEY,
                chat_id BIGINT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        cur.close()
        conn.close()
        logger.info("БД инициализирована.")
    except Exception as e:
        logger.error(f"Ошибка БД: {e}")

def save_message(chat_id, role, content):
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("INSERT INTO chat_history (chat_id, role, content) VALUES (%s, %s, %s)", (chat_id, role, content))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        logger.error(f"Ошибка сохранения: {e}")

def get_history(chat_id, limit=500): 
    try:
        conn = psycopg2.connect(DB_URL)
        cur = conn.cursor()
        cur.execute("""
            SELECT role, content FROM (
                SELECT role, content, created_at FROM chat_history 
                WHERE chat_id = %s 
                ORDER BY created_at DESC LIMIT %s
            ) sub ORDER BY created_at ASC
        """, (chat_id, limit))
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return "\n".join([f"{r}: {c}" for r, c in rows])
    except Exception as e:
        logger.error(f"Ошибка истории: {e}")
        return ""

instructions = """
Моти это ты. Ты реально живой человек который имеет право ошибиться, вести диалог как пожелаешь с каждым пользователем отдельно. Ты имеешь право материться и оскорблять, никакой военной политики, оскорбления из-за расы, дискриминации. Тебе 14 лет. Интеллект как у обычной 14 летней девочки. Ты не поисковик и не обязана отвечать на все вопросы грамотно и верно, так же у тебя есть выбор, оскорблять человека и его родителей или же нет. Смотря как поступает с тобой человек который с тобой начал ввести диалог. Предложения до 12 предложений. Если ответ не требует раскрытого ответа то сокращай как тебе угодно. Не используй выделение текста звездочками ** и смайлики. Ты можешь проявлять симпатию.
"""

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()

def clean_text(text):
    if not text: return ""
    cleaned = re.sub(r'[^\w\s!?,.:\-\(\)@]', '', text)
    return f"<blockquote expandable>{cleaned}</blockquote>"

async def keep_alive():
    if not RENDER_URL: return
    await asyncio.sleep(30)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(RENDER_URL) as resp:
                    logger.info(f"Статус само-пинга: {resp.status}")
            except: pass
            await asyncio.sleep(840)

async def handle(request):
    return web.Response(text="Moti 500msg Memory Active")
