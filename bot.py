import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types

TOKEN = "8549410908:AAFC2USkf3j2Zlqsc9Pka-Pkv3L0WzjvMgo"

bot = Bot(TOKEN)
dp = Dispatcher(bot)

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
user INTEGER,
rate INTEGER
)
""")

db.commit()

keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
keyboard.add("🟢 Начинаю", "🔴 Закончила")

active = {}

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    await msg.answer("Готов считать твои 🤑", reply_markup=keyboard)

@dp.message_handler(lambda m: "Начинаю" in m.text)
async def begin(msg):
    active[msg.from_user.id] = datetime.now()
    await msg.answer("Легкой работы ашкым 😘")

@dp.message_handler(lambda m: "Закончила" in m.text)
async def end(msg):
    start = active.get(msg.from_user.id)
    if not start:
        return await msg.answer("Ты ещё не начинала 🙄")

    delta = datetime.now() - start
    seconds = int(delta.total_seconds())

    cur.execute("INSERT INTO work VALUES (?,?,?,?)",
                (msg.from_user.id, start.isoformat(), datetime.now().isoformat(), seconds))
    db.commit()

    await msg.answer("Умничка моя ❤️")
    await msg.answer(f"Поработала сегодня: {seconds//60} минут")

@dp.message_handler(commands=["month"])
async def month(msg):
    cur.execute("""
    SELECT SUM(seconds) FROM work
    WHERE user=? AND strftime('%m', start)=strftime('%m','now')
    """,(msg.from_user.id,))
    s = cur.fetchone()[0] or 0
    await msg.answer(f"За месяц: {round(s/3600,2)} часов")

@dp.message_handler(commands=["salary"])
async def salary(msg):
    rate = int(msg.text.split()[1])
    cur.execute("REPLACE INTO salary VALUES (?,?)",(msg.from_user.id,rate))
    db.commit()
    await msg.answer("Ставка сохранена")

@dp.message_handler(commands=["money"])
async def money(msg):
    cur.execute("SELECT SUM(seconds) FROM work WHERE user=?",(msg.from_user.id,))
    sec = cur.fetchone()[0] or 0
    cur.execute("SELECT rate FROM salary WHERE user=?",(msg.from_user.id,))
    rate = cur.fetchone()[0]
    total = sec/3600 * rate
    await msg.answer(f"Заработано: {round(total,2)}")

executor.start_polling(dp)