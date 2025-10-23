import os
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from dotenv import load_dotenv
import random
import json

load_dotenv()
TOKEN = os.getenv('BOT_TOKEN')
DATA_FILE='data.json'
ALLOWED_USERS=[int(x) for x in os.getenv('USERS').split(',')]

def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:  # если файл пустой
                return []
            return json.loads(content)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def restricted(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if user_id not in ALLOWED_USERS:
            await update.message.reply_text("У вас нет доступа к этому боту.")
            return
        return await func(update, context)
    return wrapper

@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Это бот для ведения списка фильмов на просмотр. Для помощи введите /help')

@restricted
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        """Доступные команды: \n
        /start - начать работу с ботом \n
        /help - показать меню помощи \n
        /list - показать список фильмов \n
        /add - добавить фильм с список \n
        /remove - убрать фильм из списка \n
        /random - выбрать случайный фильм из списка \n
        /clear - очистить весь список
        """
    )
    await update.message.reply_text(help_text)

@restricted
async def movie_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text("Список пуст...")
        return
    await update.message.reply_text("\n".join(data))

@restricted
async def add(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Пожалуйста, укажите название фильма после команды')
        return
    
    value = ' '.join(context.args)
    data = load_data()
    data.append(value)
    save_data(data)
    await update.message.reply_text(f"\033[1m {value}\033[0m добавлен в список!")

@restricted
async def remove(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text('Пожалуйста, укажите название фильма для удаления после команды')
        return
    
    data = load_data()
    if not data:
        await update.message.reply_text('Список пуст...')
        return
    
    value = ' '.join(context.args)
    data = load_data()
    if value in data:
        data.remove(value)
        save_data(data)
        await update.effective_message.reply_text(f"Удален фильм \033[1m {value}\033[0m")
    else:
        await update.effective_message.reply_text(f"Такого фильма в списке нет")

@restricted
async def get_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text('Список пуст...')
        return
    value = random.choice(data)
    await update.message.reply_text(f'Смотрим\033[1m {value}\033[0m')

@restricted
async def remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.effective_message.reply_text("Список уже пуст.")
        return

    save_data([])  # записываем пустой список в файл
    await update.effective_message.reply_text("Список фильмов полностью очищен!")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
   
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("list", movie_list))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("random", get_random))
    app.add_handler(CommandHandler("clear", remove_all))

    print("Бот запущен...")
    app.run_polling()