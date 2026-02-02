import os
import asyncio
import sqlite3
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")

bot = Bot(TOKEN)
dp = Dispatcher()

db = sqlite3.connect("work.db")
cur = db.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS work (
user INTEGER,
start TEXT,
end TEXT,
seconds INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS salary (
user INTEGER PRIMARY KEY,
rate INTEGER
)
""")

db.commit()

active = {}

kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🟢 Начинаю"), KeyboardButton(text="🔴 Закончила")]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Готов считать твои часы и деньги 🤑", reply_markup=kb)

@dp.message(lambda m: "Начинаю" in m.text)
async def begin(msg: types.Message):
    active[msg.from_user.id] = datetime.now()
    await msg.answer("Легкой работы ашкым 😘")

@dp.message(lambda m: "Закончила" in m.text)
async def end(msg: types.Message):
    start = active.get(msg.from_user.id)
    if not start:
        await msg.answer("Ты ещё не начинала 🙄")
        return

    delta = datetime.now() - start
    seconds = int(delta.total_seconds())

    cur.execute(
        "INSERT INTO work VALUES (?,?,?,?)",
        (msg.from_user.id, start.isoformat(), datetime.now().isoformat(), seconds)
    )
    db.commit()

    await msg.answer("Умничка моя ❤️")
    await msg.answer(f"Поработала сегодня: {seconds//60} минут")

@dp.message(Command("week"))
async def week(msg: types.Message):
    cur.execute("""
    SELECT SUM(seconds) FROM work
    WHERE user=? AND start >= datetime('now','-7 days')
    """,(msg.from_user.id,))
    s = cur.fetchone()[0] or 0
    await msg.answer(f"За неделю: {round(s/3600,2)} часов")

@dp.message(Command("month"))
async def month(msg: types.Message):
    cur.execute("""
    SELECT SUM(seconds) FROM work
    WHERE user=? AND strftime('%Y-%m', start)=strftime('%Y-%m','now')
    """,(msg.from_user.id,))
    s = cur.fetchone()[0] or 0
    await msg.answer(f"За месяц поработала: {round(s/3600,2)} часов")

@dp.message(Command("salary"))
async def salary(msg: types.Message):
    rate = int(msg.text.split()[1])
    cur.execute("REPLACE INTO salary VALUES (?,?)",(msg.from_user.id,rate))
    db.commit()
    await msg.answer("Ставка сохранена")

@dp.message(Command("money"))
async def money(msg: types.Message):
    cur.execute("SELECT SUM(seconds) FROM work WHERE user=?",(msg.from_user.id,))
    sec = cur.fetchone()[0] or 0
    cur.execute("SELECT rate FROM salary WHERE user=?",(msg.from_user.id,))
    row = cur.fetchone()
    rate = row[0] if row else 0
    total = sec/3600 * rate
    await msg.answer(f"Заработала за месяц: {round(total,2)} тенге")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

from threading import Thread
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

if __name__ == "__main__":
    Thread(target=run_flask).start()
    asyncio.run(main())