from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Updater, CommandHandler, CallbackContext,
    MessageHandler, Filters, CallbackQueryHandler, ConversationHandler
)

TOKEN = "YOUR_TOKEN_HERE"  # заміни на свій токен

# === Дані ===
tasks = []
user_profiles = {}
REGISTER_NAME, REGISTER_ROLE = range(2)

# === Команди ===
def start(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    if user_id not in user_profiles:
        update.message.reply_text("👤 Вітаю! Як вас звати?")
        return REGISTER_NAME
    update.message.reply_text("👋 Вітаю! Команди:\n/new <завдання>\n/list\n/pay <сума>\n/report – підсумок")
    return ConversationHandler.END

def register_name(update: Update, context: CallbackContext):
    context.user_data['name'] = update.message.text
    update.message.reply_text("🧩 Яка ваша роль? (наприклад: виконавець, координатор)")
    return REGISTER_ROLE

def register_role(update: Update, context: CallbackContext):
    user_id = update.effective_user.id
    name = context.user_data['name']
    role = update.message.text
    user_profiles[user_id] = {
        'name': name,
        'role': role,
        'username': update.effective_user.username,
        'completed_tasks': 0,
        'earned': 0.0
    }
    update.message.reply_text(f"✅ Зареєстровано як {name} ({role})\nМожна працювати 🙂")
    return ConversationHandler.END

def new_task(update: Update, context: CallbackContext):
    text = ' '.join(context.args)
    if not text:
        update.message.reply_text("❗️ Напиши завдання після /new")
        return
    tasks.append({'text': text, 'status': 'нове', 'user': None, 'proof': None})
    update.message.reply_text("✅ Завдання додано!")

def list_tasks(update: Update, context: CallbackContext):
    if not tasks:
        update.message.reply_text("📭 Завдань немає.")
        return
    for i, t in enumerate(tasks):
        msg = f"📌 {t['text']}\nСтан: {t['status']}"
        buttons = []
        if t['status'] == 'нове':
            buttons.append(InlineKeyboardButton("🔧 Взятись", callback_data=f"take_{i}"))
        if t['status'] == 'в роботі' and t['user'] == update.effective_user.first_name:
            buttons.append(InlineKeyboardButton("📤 Додати підтвердження", callback_data=f"proof_{i}"))
        if t['status'] == 'на перевірці':
            buttons.append(InlineKeyboardButton("✅ Підтвердити", callback_data=f"confirm_{i}"))
        update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup.from_button(buttons) if buttons else None)

def button_callback(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    action, idx = query.data.split("_")
    idx = int(idx)
    task = tasks[idx]
    uid = query.from_user.id

    if action == "take":
        task['status'] = 'в роботі'
        task['user'] = uid
        query.edit_message_text(f"🔧 {task['text']}\nВиконує: {user_profiles.get(uid, {}).get('name', '??')}")
    elif action == "proof":
        context.user_data['pending_proof'] = idx
        query.message.reply_text(f"📎 Надішліть підтвердження виконання завдання: {task['text']}")
    elif action == "confirm":
        task['status'] = 'завершено'
        user_id = task['user']
        if user_id in user_profiles:
            user_profiles[user_id]['completed_tasks'] += 1
        query.edit_message_text(f"✅ Завершено: {task['text']}")

def handle_proof(update: Update, context: CallbackContext):
    if 'pending_proof' in context.user_data:
        idx = context.user_data.pop('pending_proof')
        tasks[idx]['status'] = 'на перевірці'
        tasks[idx]['proof'] = True
        update.message.reply_text("📥 Підтвердження прийнято. Очікує перевірки.")

def pay(update: Update, context: CallbackContext):
    try:
        amount = float(context.args[0])
    except:
        update.message.reply_text("❗️ Напиши суму після /pay, наприклад: /pay 300")
        return

    done_tasks = [t for t in tasks if t['status'] == 'завершено']
    people = list(set(t['user'] for t in done_tasks if t['user']))
    count = len(people)

    if count == 0:
        update.message.reply_text("Немає підтверджених виконавців.")
        return

    if count == 1:
        share = round(amount * 0.8, 2)
    elif count == 2:
        share = round(amount * 0.4, 2)
    elif count == 3:
        share = round(amount * 0.3, 2)
    else:
        share = round(amount / count, 2)

    text = "💸 Розподіл оплати:\n"
    for uid in people:
        if uid in user_profiles:
            user_profiles[uid]['earned'] += share
            name = user_profiles[uid]['name']
            text += f"{name} — {share} грн\n"
    update.message.reply_text(text)

def report(update: Update, context: CallbackContext):
    text = "📊 Підсумок по користувачах:\n"
    for uid, profile in user_profiles.items():
        text += (
            f"{profile['name']} ({profile['role']}) — "
            f"{profile['completed_tasks']} задач, "
            f"{profile['earned']} грн\n"
        )
    update.message.reply_text(text)

# === Головна ===
def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher

    reg = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            REGISTER_NAME: [MessageHandler(Filters.text & ~Filters.command, register_name)],
            REGISTER_ROLE: [MessageHandler(Filters.text & ~Filters.command, register_role)],
        },
        fallbacks=[],
    )

    dp.add_handler(reg)
    dp.add_handler(CommandHandler("new", new_task))
    dp.add_handler(CommandHandler("list", list_tasks))
    dp.add_handler(CommandHandler("pay", pay))
    dp.add_handler(CommandHandler("report", report))
    dp.add_handler(CallbackQueryHandler(button_callback))
    dp.add_handler(MessageHandler(Filters.text | Filters.photo | Filters.document, handle_proof))

    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
