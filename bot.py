from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json
import os

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_TOKEN_HERE")
DATA_FILE = 'tasks.json'
USER_FILE = 'users.json'
ADMIN_IDS = [1192117081]

def load_json(path, default):
    if not os.path.exists(path):
        with open(path, 'w') as f:
            json.dump(default, f)
    with open(path, 'r') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users = load_json(USER_FILE, {})
    uid = str(update.effective_user.id)
    if uid not in users:
        users[uid] = {"name": update.effective_user.first_name}
        save_json(USER_FILE, users)
        await update.message.reply_text("Привіт! Тебе зареєстровано.")
    else:
        await update.message.reply_text("Ти вже зареєстрований.")

async def new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = " ".join(context.args)
    if not text:
        await update.message.reply_text("Введи опис задачі після /new")
        return
    tasks = load_json(DATA_FILE, [])
    tasks.append({"user_id": update.effective_user.id, "text": text, "status": "pending"})
    save_json(DATA_FILE, tasks)
    await update.message.reply_text("Задача додана!")

async def list_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tasks = load_json(DATA_FILE, [])
    if not tasks:
        await update.message.reply_text("Немає задач.")
        return
    text = "\n".join([f"{i+1}. {t['text']} - {t['status']}" for i, t in enumerate(tasks)])
    await update.message.reply_text(text)

async def confirm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Немає доступу.")
        return
    tasks = load_json(DATA_FILE, [])
    for task in tasks:
        if task['status'] == 'pending':
            task['status'] = 'confirmed'
    save_json(DATA_FILE, tasks)
    await update.message.reply_text("Підтверджено!")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("new", new))
    app.add_handler(CommandHandler("list", list_tasks))
    app.add_handler(CommandHandler("confirm", confirm))
    app.run_polling()

if __name__ == '__main__':
    main()
