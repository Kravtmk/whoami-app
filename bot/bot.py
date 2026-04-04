import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes



TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
API = os.environ.get("API_BASE_URL", "http://api:8000").rstrip("/")
AI_API = os.environ.get("AI_API_URL", "http://whoami-ai:8001").rstrip("/")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🦝 Енот Рикки на связи!\n"
        "Команды:\n"
        "/today <userId>\n"
        "/add <userId> <roleId> <minutes>\n\n"
        "Или просто напиши мне что-нибудь!"
    )

def upsert_user_from_update(update: Update):
    tg = update.effective_user
    if not tg:
        return

    telegram_id = tg.id
    display_name = tg.full_name  # или tg.first_name

    requests.post(
        f"{API}/users/upsert",
        json={"telegramId": telegram_id, "displayName": display_name},
        timeout=10,
    )
    
async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):

    telegram_id = update.effective_user.id
    display_name = update.effective_user.full_name

    r = requests.get(
        f"{API}/today",
        params={
            "telegramId": telegram_id,
            "displayName": display_name
        },
        timeout=10
    )

    r.raise_for_status()
    data = r.json()

    other = data.get("otherMinutes")
    summary = data.get("summaryPercent", {})

    msg = (
        f"📅 Today\n"
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
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), chat))
    app.run_polling()


async def chat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    text = update.message.text

    try:        
        response = requests.post(
            f"{AI_API}/chat", 
            json={"user_id": user_id, "text": text},
            timeout=10
        )
        response.raise_for_status()
        reply = response.json().get("reply", "Енот задумался...")
        await update.message.reply_text(reply)
    except Exception as e:
        print(f"AI Error: {e}")
        await update.message.reply_text("🦝🔌 Ой, я отвлекся на аранчини... попробуй еще раз!")


if __name__ == "__main__":
    main()