import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.constants import ParseMode
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from dotenv import load_dotenv
import random
import json
import asyncio

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
    keyboard = [
        ["/list", "/add", "/remove"],
        ["/random", "/clear", "/hat"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "Привет! Выберите действие 👇",
        reply_markup=reply_markup
    )

@restricted
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        """Доступные команды: \n
        /start - начать работу с ботом \n
        /help - показать меню помощи \n
        /list - показать список фильмов \n
        /add - добавить фильм в список \n
        /remove - убрать фильм из списка \n
        /random - выбрать случайный фильм из списка \n
        /clear - очистить весь список \n
        /hat - игра в шляпу с фильмами
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
    await update.message.reply_text(f"*{value}* добавлен в список!", parse_mode='Markdown')

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
        await update.effective_message.reply_text(f"Удален фильм *{value}*", parse_mode='Markdown')
    else:
        await update.effective_message.reply_text(f"Такого фильма в списке нет")

@restricted
async def get_random(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.message.reply_text('Список пуст...')
        return
    value = random.choice(data)
    await update.message.reply_text(f'Смотрим *{value}*', parse_mode='Markdown')

@restricted
async def remove_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = load_data()
    if not data:
        await update.effective_message.reply_text("Список уже пуст.")
        return

    save_data([])  # записываем пустой список в файл
    await update.effective_message.reply_text("Список фильмов полностью очищен!")

@restricted 
async def hat(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Введите количество людей')
    context.user_data['state'] = 'waiting_for_count'

@restricted 
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')

    if state == 'waiting_for_count':
        try:
            count = int(update.message.text)
        except ValueError:
            await update.message.reply_text('Введите число')
            return

        context.user_data['count'] = count
        context.user_data['films'] = []
        context.user_data['state'] = 'waiting_for_films'

        await update.message.reply_text(f'Теперь введите {count} фильмов (по одному сообщению)')
        return

    elif state == 'waiting_for_films':
        film = update.message.text.strip()
        context.user_data['films'].append(film)
        remaining = context.user_data['count'] - len(context.user_data['films'])

        if remaining > 0:
            await update.message.reply_text(f'Добавлен фильм <tg-spoiler>{film}</tg-spoiler>. Осталось ввести ещё {remaining} фильмов', parse_mode=ParseMode.HTML)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)    
        else:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=update.message.message_id)   
            await update.message.reply_text('Начинаем отбор фильма...')
            await asyncio.sleep(1)

            films = context.user_data['films']
            while len(films) > 1:
                value = random.choice(films)
                films.remove(value)
                await update.message.reply_text(f'Выбывает *{value}*', parse_mode='Markdown')
                await asyncio.sleep(1)
            winner = films[0]
            await update.message.reply_text(f'🏆 Победитель: *{winner}*!', parse_mode='Markdown')
            context.user_data.clear()

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
   
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("list", movie_list))
    app.add_handler(CommandHandler("add", add))
    app.add_handler(CommandHandler("remove", remove))
    app.add_handler(CommandHandler("random", get_random))
    app.add_handler(CommandHandler("clear", remove_all))
    app.add_handler(CommandHandler("hat", hat))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот запущен...")
    app.run_polling()