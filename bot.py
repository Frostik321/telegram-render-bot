import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise RuntimeError("TOKEN is not set")

TASKS = []

def get_user_active_task(user_name):
    for i, task in enumerate(TASKS):
        if task["status"] == "зайнята" and task["by"] == user_name:
            return i
    return None

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Привіт! /new – додати задачу, /list – подивитися задачі.")

def new_task(update: Update, context: CallbackContext):
    if context.args:
        task_text = " ".join(context.args)
        TASKS.append({"text": task_text, "status": "вільна", "by": None, "proof": None})
        update.message.reply_text(f"✅ Задачу додано: {task_text}")
    else:
        update.message.reply_text("❗️Використання: /new опис задачі")

def list_tasks(update: Update, context: CallbackContext):
    if not TASKS:
        return update.message.reply_text("🔍 Поки що задач немає.")
    for i, task in enumerate(TASKS):
        stat = "🟢 Вільна" if task["status"]=="вільна" else f"🔴 Зайнята: {task['by']}" if task["status"]=="зайнята" else f"✅ Виконано: {task['by']}"
        msg = f"📌 {task['text']}\nСтатус: {stat}"
        if task["proof"]: msg += f"\n📎 Підтвердження: {task['proof']}"
        btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Взяти в роботу", callback_data=f"take_{i}")]]) if task["status"]=="вільна" else None
        update.message.reply_text(msg, reply_markup=btn)

def button_cb(update: Update, context: CallbackContext):
    q = update.callback_query; q.answer()
    idx = int(q.data.split("_")[1])
    task = TASKS[idx]
    if task["status"] != "вільна":
        q.edit_message_text(f"⚠️ Зайнято: {task['by']}")
        return
    task["status"] = "зайнята"
    task["by"] = q.from_user.first_name
    q.edit_message_text(f"🛠️ {task['text']}\n🔒 Взято в роботу: {task['by']}")

def proof(update: Update, context: CallbackContext):
    u = update.message.from_user.first_name
    idx = get_user_active_task(u)
    if idx is None:
        return update.message.reply_text("❗️У вас немає активних задач.")
    task = TASKS[idx]
    if update.message.text:
        proof_text = update.message.text
    elif update.message.photo:
        proof_text = f"[фото від {u}]"
    elif update.message.document:
        proof_text = f"[файл: {update.message.document.file_name}]"
    else:
        proof_text = "[підтвердження]"
    task["proof"] = proof_text
    task["status"] = "виконано"
    update.message.reply_text(f"✅ Задача виконана: {task['text']}\n📎 {proof_text}")

def main():
    updater = Updater(TOKEN, use_context=True)_
