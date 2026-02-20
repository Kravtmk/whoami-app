import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API = os.environ.get("API_BASE_URL", "http://api:8000").rstrip("/")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "WhoAmI bot online 😎\n"
        "Команды:\n"
        "/today <userId>\n"
        "/add <userId> <roleId> <minutes>\n"
        "Пример: /add u1 1 25"
    )

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Пример: /today u1")
        return

    user_id = context.args[0]
    r = requests.get(f"{API}/today", params={"userId": user_id}, timeout=10)
    r.raise_for_status()
    data = r.json()

    other = data.get("otherMinutes")
    summary = data.get("summaryPercent", {})
    msg = (
        f"📅 Today for {user_id}\n"
        f"Other minutes: {other}\n"
        f"Sleep: {summary.get('sleep')}%\n"
        f"Buffer: {summary.get('buffer')}%\n"
        f"Tracked: {summary.get('tracked')}%\n"
        f"Other: {summary.get('other')}%\n"
    )
    await update.message.reply_text(msg)

async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Пример: /add u1 1 25")
        return

    user_id = context.args[0]
    role_id = int(context.args[1])
    minutes = int(context.args[2])

    payload = {"roleId": role_id, "minutes": minutes}
    r = requests.post(f"{API}/today/segment", params={"userId": user_id}, json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()

    await update.message.reply_text(
        f"✅ Added: roleId={role_id}, minutes={minutes}\n"
        f"Other minutes now: {data.get('otherMinutes')}"
    )

def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("add", add))
    app.run_polling()

if __name__ == "__main__":
    main()