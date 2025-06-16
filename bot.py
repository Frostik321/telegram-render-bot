from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import json
import os

# Конфігурація
DATA_FILE = 'data.json'
USER_FILE = 'users.json'
ADMIN_IDS = [1192117081]  # Ваш Telegram ID
BOT_TOKEN = "7689001833:AAFIz0y9Z-WdjBT93mtC8dN-8uPIzVGXYRg"

# Ініціалізація файлів
for file in [DATA_FILE, USER_FILE]:
    if not os.path.exists(file):
        with open(file, 'w') as f:
            json.dump([] if file == DATA_FILE else {}, f)

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_users():
    try:
        with open(USER_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return {}

def save_users(users):
    with open(USER_FILE, 'w') as f:
        json.dump(users, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    users = load_users()
    if str(user.id) not in users:
        users[str(user.id)] = {
            "name": user.first_name,
            "username": user.username or "",
            "role": "виконавець"
        }
        save_users(users)
        await update.message.reply_text("👋 Привіт! Тебе зареєстровано. Напиши /new <завдання>, щоб додати.")
    else:
        await update.message.reply_text("👋 Ти вже зареєстрований.")

async def new_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("❗️ Напиши задачу після команди /new")
        return
    
    data = load_data()
    data.append({
        "text": text,
        "user_id": update.effective_user.id,
        "status": "pending",
        "confirmed": False
    })
    save_data(data)
    await update.message.reply_text("✅ Завдання додано та очікує перевірки.")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    await update.message.reply_text(
        "🕳 Немає жодної задачі." if not data else 
        "\n".join(f"{i+1}. 📌 {t['text']} — {t['status']}" for i, t in enumerate(data))
    )

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ У вас немає прав для цієї команди.")
        return
    
    data = load_data()
    count = sum(1 for t in data if t["status"] == "pending")
    for t in data:
        if t["status"] == "pending":
            t.update({"status": "approved", "confirmed": True})
    save_data(data)
    await update.message.reply_text(f"✅ Підтверджено {count} задач.")

async def report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔️ У вас немає прав для цієї команди.")
        return
    
    data = load_data()
    users = load_users()
    payouts = {}
    for t in filter(lambda x: x["confirmed"], data):
        uid = str(t["user_id"])
        payouts[uid] = payouts.get(uid, 0) + 1

    await update.message.reply_text(
        "💰 Звіт по оплаті:\n" + 
        "\n".join(f"{users.get(uid, {}).get('name', 'невідомо')} — {count * 100} грн" 
        for uid, count in payouts.items())
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new_task))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("confirm", confirm))
    app.add_handler(CommandHandler("report", report))
    app.run_polling()

if __name__ == '__main__':
    main()
