import logging
import asyncio
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

# ===== НАСТРОЙКИ =====
BOT_TOKEN = "8959341115:AAFqmyHEwdWOvr8CQySjrHvzJMYSd5dGhEA"
BISHKEK_TZ = ZoneInfo("Asia/Bishkek")

# Состояния диалога
WAITING_BIRTHDAY = 1

# Хранилище пользователей
users = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def days_lived(birthday_str: str) -> int:
    birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()
    today = date.today()
    return (today - birthday).days


def get_motivation(days: int) -> str:
    if days % 1000 == 0:
        return f"🎊 Вау! Ровно {days:,} дней — это особенный день!"
    elif days % 100 == 0:
        return f"✨ Красивое число — {days:,} дней!"
    elif days < 7300:
        return "🌱 Ты ещё молод — впереди целая жизнь!"
    elif days < 14600:
        return "💪 Самое продуктивное время жизни — используй его!"
    elif days < 21900:
        return "🌟 Мудрость и опыт — твоё главное богатство!"
    else:
        return "👑 Ты настоящий ветеран жизни — уважение!"


def build_daily_message(birthday_str: str) -> str:
    days = days_lived(birthday_str)
    motivation = get_motivation(days)
    today = datetime.now(BISHKEK_TZ).strftime("%d.%m.%Y")
    return (
        f"🌅 *Доброе утро!*\n\n"
        f"📅 Сегодня: {today}\n"
        f"🔢 Ты прожил уже *{days:,} дней*!\n\n"
        f"{motivation}\n\n"
        f"Удачного дня! 🚀"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in users:
        days = days_lived(users[chat_id])
        await update.message.reply_text(
            f"👋 Привет! Ты уже зарегистрирован.\n"
            f"🔢 Ты прожил *{days:,} дней*!\n\n"
            f"Каждый день в 8:00 по Бишкеку я буду присылать тебе сообщение.\n\n"
            f"Чтобы изменить дату рождения — напиши /setbirthday",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "👋 *Привет! Я твой счётчик дней жизни!*\n\n"
        "Каждое утро в *8:00 по Бишкеку* я буду присылать тебе:\n"
        "• Сколько дней ты прожил 🔢\n"
        "• Мотивацию на день 💪\n\n"
        "Введи свою дату рождения в формате:\n"
        "*ДД.ММ.ГГГГ*\n\nНапример: `15.03.1995`",
        parse_mode="Markdown"
    )
    return WAITING_BIRTHDAY


async def set_birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 Введи новую дату рождения в формате:\n*ДД.ММ.ГГГГ*\n\nНапример: `15.03.1995`",
        parse_mode="Markdown"
    )
    return WAITING_BIRTHDAY


async def receive_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id

    try:
        birthday = datetime.strptime(text, "%d.%m.%Y").date()
        if birthday > date.today():
            await update.message.reply_text("❌ Дата рождения не может быть в будущем!\nПопробуй ещё раз:")
            return WAITING_BIRTHDAY
        if (date.today() - birthday).days > 365 * 120:
            await update.message.reply_text("❌ Слишком старая дата. Попробуй ещё раз:")
            return WAITING_BIRTHDAY

        users[chat_id] = text
        days = days_lived(text)

        await update.message.reply_text(
            f"✅ *Отлично! Дата сохранена!*\n\n"
            f"🎂 День рождения: {text}\n"
            f"🔢 Ты прожил уже *{days:,} дней*!\n\n"
            f"Каждый день в *8:00 по Бишкеку* я буду присылать тебе сообщение 🌅\n\n"
            f"Команды:\n"
            f"/today — узнать счёт прямо сейчас\n"
            f"/setbirthday — изменить дату рождения\n"
            f"/stop — отключить уведомления",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат даты!\n\nВведи в формате *ДД.ММ.ГГГГ*\nНапример: `15.03.1995`",
            parse_mode="Markdown"
        )
        return WAITING_BIRTHDAY


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in users:
        await update.message.reply_text("❗ Сначала зарегистрируйся! Напиши /start")
        return
    message = build_daily_message(users[chat_id])
    await update.message.reply_text(message, parse_mode="Markdown")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in users:
        del users[chat_id]
        await update.message.reply_text("😔 Уведомления отключены.\n\nЧтобы снова включить — напиши /start")
    else:
        await update.message.reply_text("Ты ещё не зарегистрирован. Напиши /start")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отменено. Напиши /start чтобы начать заново.")
    return ConversationHandler.END


async def send_daily_messages(context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Отправка утренних сообщений. Пользователей: {len(users)}")
    for chat_id, birthday_str in list(users.items()):
        try:
            message = build_daily_message(birthday_str)
            await context.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
            logger.info(f"Сообщение отправлено: {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка отправки {chat_id}: {e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("setbirthday", set_birthday_command),
        ],
        states={
            WAITING_BIRTHDAY: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_birthday)
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("stop", stop_command))

    # Каждый день в 8:00 по Бишкеку = 02:00 UTC
    job_queue = app.job_queue
    job_queue.run_daily(
        send_daily_messages,
        time=time(hour=2, minute=0, tzinfo=ZoneInfo("UTC")),
        name="daily_message"
    )

    logger.info("Бот запущен!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
