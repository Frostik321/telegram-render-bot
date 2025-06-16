import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackContext, MessageHandler, Filters, CallbackQueryHandler

TOKEN = os.getenv("TOKEN")
TASKS = []

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Привіт! Команди:\n/new <текст задачі>\n/list – список задач\n/pending – на перевірку\n/pay <сума> – розрахувати оплату")

def new_task(update: Update, context: CallbackContext):
    if not context.args:
        return update.message.reply_text("Використання: /new <опис задачі>")
    text = " ".join(context.args)
    TASKS.append({"text": text, "status": "вільна", "by": [], "proof": [], "approved": False})
    update.message.reply_text(f"✅ Додано задачу: {text}")

def list_tasks(update: Update, context: CallbackContext):
    if not TASKS:
        return update.message.reply_text("Задач немає.")
    for i, t in enumerate(TASKS):
        s = t["status"]
        workers = ", ".join(t["by"]) if t["by"] else "-"
        msg = f"📌 {t['text']}\n👥 Виконують: {workers}\n📎 Підтверджень: {len(t['proof'])}\n✅ Підтверджено: {t['approved']}\nСтатус: {s}"
        if s == "вільна":
            btn = InlineKeyboardMarkup([[InlineKeyboardButton("✅ Взяти", callback_data=f"take_{i}")]])
        else:
            btn = None
        update.message.reply_text(msg, reply_markup=btn)

def button_cb(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    if q.data.startswith("take_"):
        i = int(q.data.split("_")[1])
        user = q.from_user.first_name
        if TASKS[i]["status"] == "вільна":
            TASKS[i]["status"] = "в роботі"
            TASKS[i]["by"].append(user)
        elif user not in TASKS[i]["by"]:
            TASKS[i]["by"].append(user)
        q.edit_message_text(f"🔧 Задача: {TASKS[i]['text']}\n👥 Тепер виконує: {', '.join(TASKS[i]['by'])}")

def proof(update: Update, context: CallbackContext):
    user = update.message.from_user.first_name
    for i, t in enumerate(TASKS):
        if user in t["by"] and t["status"] == "в роботі":
            text = update.message.text or "[файл/фото]"
            if update.message.photo:
                text = "[Фото]"
            elif update.message.document:
                text = f"[Файл: {update.message.document.file_name}]"
            t["proof"].append(f"{user}: {text}")
            t["status"] = "очікує перевірки"
            update.message.reply_text(f"✅ Підтвердження додано для задачі: {t['text']}")
            return
    update.message.reply_text("❗️У вас немає активної задачі або вона вже перевіряється.")

def pending(update: Update, context: CallbackContext):
    for i, t in enumerate(TASKS):
        if t["status"] == "очікує перевірки" and not t["approved"]:
            msg = f"🕵 Перевірка задачі: {t['text']}\n👥 Виконавці: {', '.join(t['by'])}\n📎 Підтвердження:"
            for p in t["proof"]:
                msg += f"\n— {p}"
            btn = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Прийняти", callback_data=f"approve_{i}"),
                 InlineKeyboardButton("❌ Відхилити", callback_data=f"reject_{i}")]
            ])
            update.message.reply_text(msg, reply_markup=btn)

def approve_reject_cb(update: Update, context: CallbackContext):
    q = update.callback_query
    q.answer()
    if q.data.startswith("approve_") or q.data.startswith("reject_"):
        i = int(q.data.split("_")[1])
        decision = q.data.split("_")[0]
        TASKS[i]["approved"] = (decision == "approve")
        TASKS[i]["status"] = "виконано" if decision == "approve" else "в роботі"
        text = "✅ Прийнято" if decision == "approve" else "❌ Відхилено"
        q.edit_message_text(f"{text} задача: {TASKS[i]['text']}")

def pay(update: Update, context: CallbackContext):
    if not context.args or not context.args[0].isdigit():
        return update.message.reply_text("Використання: /pay <сума>")
    total = int(context.args[0])
    for t in TASKS:
        if t["status"] == "виконано" and t["approved"]:
            count = len(t["by"])
            if count == 1:
                percent = 80
            elif count == 2:
                percent = 40
            else:
                percent = 30
            share = round(total * percent / 100, 2)
            msg = f"💸 Оплата задачі: {t['text']}\n"
            for u in t["by"]:
                msg += f"— {u}: {share}€\n"
            update.message.reply_text(msg)

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("new", new_task))
    dp.add_handler(CommandHandler("list", list_tasks))
    dp.add_handler(CommandHandler("pending", pending))
    dp.add_handler(CommandHandler("pay", pay))
    dp.add_handler(CallbackQueryHandler(button_cb, pattern="^take_"))
    dp.add_handler(CallbackQueryHandler(approve_reject_cb, pattern="^(approve|reject)_"))
    dp.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, proof))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
