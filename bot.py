import os
import json
import gspread
from google.oauth2.service_account import Credentials
import asyncio
from datetime import datetime

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")

creds_dict = json.loads(GOOGLE_CREDENTIALS)

scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_info(creds_dict, scopes=scopes)

gc = gspread.authorize(credentials)
sheet = gc.open_by_key(SHEET_ID).sheet1
def get_user_rows(user_id):
    rows = sheet.get_all_records()
    return [r for r in rows if str(r["user_id"]) == str(user_id)]

bot = Bot(TOKEN)
dp = Dispatcher()

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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sheet.append_row([
        msg.from_user.id,
        now,
        "",
        ""
    ])

    await msg.answer("Легкой работы ашкым 😘")
    
@dp.message(lambda m: "Закончила" in m.text)
async def end(msg: types.Message):
    records = sheet.get_all_records()

    for i in range(len(records) - 1, -1, -1):
        row = records[i]
        if str(row["user_id"]) == str(msg.from_user.id) and row["end"] == "":
            start_time = datetime.strptime(row["start"], "%Y-%m-%d %H:%M:%S")
            end_time = datetime.now()
            minutes = int((end_time - start_time).total_seconds() / 60)

            sheet.update_cell(i + 2, 3, end_time.strftime("%Y-%m-%d %H:%M:%S"))
            sheet.update_cell(i + 2, 4, minutes)

            await msg.answer("Умничка моя ❤️")
            await msg.answer(f"Поработала сегодня: {minutes} минут")
            return

    await msg.answer("Ты ещё не начинала 🙄")

@dp.message(Command("week"))
async def week(msg: types.Message):
    records = sheet.get_all_records()
    total_minutes = 0

    now = datetime.now()

    for row in records:
        if str(row["user_id"]) == str(msg.from_user.id) and row["end"]:
            start = datetime.strptime(row["start"], "%Y-%m-%d %H:%M:%S")

            if (now - start).days <= 7:
                total_minutes += int(row["minutes"])

    await msg.answer(f"За неделю поработала: {round(total_minutes/60,2)} часов")

@dp.message(Command("month"))
async def month(msg: types.Message):
    rows = get_user_rows(msg.from_user.id)

    now = datetime.now()
    total_minutes = 0

    for r in rows:
        if r["end"]:
            start = datetime.strptime(r["start"], "%Y-%m-%d %H:%M:%S")
            if start.month == now.month and start.year == now.year:
                total_minutes += int(r["minutes"])

    await msg.answer(f"За месяц поработала: {round(total_minutes/60,2)} часов")


@dp.message(Command("salary"))
async def salary(msg: types.Message):
    rate = int(msg.text.split()[1])

    rows = sheet.get_all_records()

    for i, r in enumerate(rows):
        if str(r["user_id"]) == str(msg.from_user.id):
            sheet.update_cell(i+2,5,rate)
            await msg.answer("Ставка сохранена")
            return

    sheet.append_row([msg.from_user.id,"","","",rate])
    await msg.answer("Ставка сохранена")


@dp.message(Command("money"))
async def money(msg: types.Message):
    rows = get_user_rows(msg.from_user.id)

    total_minutes = 0
    rate = 0

    now = datetime.now()

    for r in rows:
        if r.get("rate"):
            rate = int(r["rate"])

        if r["end"]:
            start = datetime.strptime(r["start"], "%Y-%m-%d %H:%M:%S")
            if start.month == now.month and start.year == now.year:
                total_minutes += int(r["minutes"])

    total = (total_minutes/60) * rate
    await msg.answer(f"Заработала за месяц: {round(total,2)} тенге")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())