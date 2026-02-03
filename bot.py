import os
import json
import gspread
from google.oauth2.service_account import Credentials
import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

TOKEN = os.getenv("TOKEN")
SHEET_ID = os.getenv("SHEET_ID")
GOOGLE_CREDENTIALS = os.getenv("GOOGLE_CREDENTIALS")
TIME_FORMAT = "%Y-%m-%d %H:%M:%S"
TZ = ZoneInfo("Asia/Almaty")
print(datetime.now(TZ))

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
        [
            KeyboardButton(text="🟢 Начинаю"),
            KeyboardButton(text="🔴 Закончила")
        ],
        [
            KeyboardButton(text="📅 Неделя"),
            KeyboardButton(text="🗓 Месяц"),
            KeyboardButton(text="💰 Деньги")
        ]
    ],
    resize_keyboard=True
)

@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer("Готов считать твои часы и деньги 🤑", reply_markup=kb)

@dp.message(lambda m: "Начинаю" in m.text)
async def begin(msg: types.Message):
    records = sheet.get_all_records()

    for r in records:
        if str(r["user_id"]) == str(msg.from_user.id) and not r.get("end"):
            await msg.answer("Ты уже на смене 🙄")
            return

    now = datetime.now(TZ).strftime(TIME_FORMAT)

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
            start = datetime.strptime(
            row["start"],
            TIME_FORMAT
            ).replace(tzinfo=TZ)
            end = datetime.now(TZ)
            minutes = int((end - start).total_seconds() / 60)
            hours = minutes // 60
            mins = minutes % 60

            sheet.update_cell(i + 2, 3, end.strftime(TIME_FORMAT))
            sheet.update_cell(i + 2, 4, minutes)

            await msg.answer(
            f"""
            Поработала сегодня: {hours} часов {mins} минут

            Умничка моя ❤️
            Теперь отдыхай 🥰
            """
            )
            return

    await msg.answer("Ты ещё не начинала 🙄")


@dp.message(lambda m: "Неделя" in m.text)
async def week(msg: types.Message):
    rows = get_user_rows(msg.from_user.id)

    now = datetime.now(TZ)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(hour=0, minute=0, second=0)

    days = {}

    for r in rows:
        if r["end"]:
            start = datetime.strptime(
            r["start"],
            TIME_FORMAT
            ).replace(tzinfo=TZ)

            if start >= week_start:
                d = start.strftime("%d.%m")
                days[d] = days.get(d, 0) + int(r["minutes"])

    text = "📅 За эту неделю:\n\n"
    total = 0

    for d in sorted(days):
        mins = days[d]
        h = mins // 60
        m = mins % 60
        text += f"{d} — {h}ч {m}м\n"
        total += mins

    th = total // 60
    tm = total % 60

    text += f"\n────────────\nИтого: {th} часов {tm} минут\n\nТак держать милая 😽"

    await msg.answer(text)


@dp.message(lambda m: "Месяц" in m.text)
async def month(msg: types.Message):
    rows = get_user_rows(msg.from_user.id)

    now = datetime.now(TZ)
    first_day = now.replace(day=1)

    weeks = {}

    for r in rows:
        if r["end"]:
            start = datetime.strptime(
            r["start"],
            TIME_FORMAT
            ).replace(tzinfo=TZ)

            if start.month == now.month and start.year == now.year:
                week_num = ((start.day - 1) // 7) + 1
                weeks[week_num] = weeks.get(week_num, 0) + int(r["minutes"])

    text = f"🗓 {now.strftime('%B')}:\n\n"
    total = 0

    for w in sorted(weeks):
        mins = weeks[w]
        h = mins // 60
        m = mins % 60
        text += f"Неделя {w} — {h}ч {m}м\n"
        total += mins

    th = total // 60
    tm = total % 60

    text += f"\n────────────\nИтого: {th} часов {tm} минут\n\nТак держать милая 😽"

    await msg.answer(text)



@dp.message(lambda m: "Деньги" in m.text)
async def money(msg: types.Message):
    records = sheet.get_all_records()

    now = datetime.now(TZ)
    total_minutes = 0
    rate = 0

    for r in records:
     if str(r["user_id"]) == str(msg.from_user.id):

        if r.get("rate"):
            rate = int(r["rate"])

        if r["end"]:
            start = datetime.strptime(
            r["start"],
            TIME_FORMAT
            ).replace(tzinfo=TZ)
            if start.month == now.month and start.year == now.year:
                total_minutes += int(r["minutes"])


    hours = total_minutes // 60
    mins = total_minutes % 60

    total = round((total_minutes / 60) * rate, 2)

    await msg.answer(
f"""
🌸 Отчёт

В этом месяце ты поработала:
⏳ {hours} часов {mins} минут

Заработала:
💰 {total} тенге

Горжусь ❤️

P.S. Только не потрать все сразу 😂
"""
)


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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())