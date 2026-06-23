import logging
from datetime import datetime, date, time
from zoneinfo import ZoneInfo
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)

BOT_TOKEN = "8959341115:AAFqmyHEwdWOvr8CQySjrHvzJMYSd5dGhEA"
BISHKEK_TZ = ZoneInfo("Asia/Bishkek")
WAITING_BIRTHDAY = 1

users = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def days_lived(birthday_str: str) -> int:
    birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()
    return (date.today() - birthday).days


def days_to_next_year(birthday_str: str) -> int:
    birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()
    today = date.today()
    next_birthday = birthday.replace(year=today.year)
    if next_birthday <= today:
        next_birthday = next_birthday.replace(year=today.year + 1)
    return (next_birthday - today).days


def get_age(birthday_str: str) -> tuple:
    """Возвращает (полных лет, дней после последнего дня рождения)"""
    birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()
    today = date.today()
    years = today.year - birthday.year
    last_birthday = birthday.replace(year=today.year)
    if last_birthday > today:
        years -= 1
        last_birthday = birthday.replace(year=today.year - 1)
    days_since = (today - last_birthday).days
    return years, days_since


MOTIVATIONS = [
    "💪 Каждый день — это новый шанс стать лучше. Используй его!",
    "🔥 Ты уже столько прошёл — не останавливайся сейчас!",
    "🌟 Великие дела начинаются с маленьких шагов. Сделай свой шаг сегодня!",
    "🚀 Твоё будущее создаётся прямо сейчас. Действуй!",
    "⚡ Энергия, фокус, результат — сегодня твой день!",
    "🎯 У тебя есть цель? Иди к ней. Нет цели? Найди её сегодня!",
    "🌈 После любой бури приходит солнце. Улыбнись новому дню!",
    "💡 Умные люди учатся каждый день. Чему научишься сегодня?",
    "🏆 Победители не рождаются — они делают выбор каждое утро. Ты выбираешь победу?",
    "🌱 Расти каждый день — даже на 1% лучше. Год пройдёт — ты станешь в 37 раз лучше!",
    "💎 Алмаз — это уголь, который выдержал давление. Держись!",
    "🦁 Просыпайся как лев — голодный до успеха!",
    "⭐ Твои мечты не случайны — они даны тебе не зря. Верь в себя!",
    "🎸 Живи так, чтобы было что вспомнить. Сделай сегодня незабываемым!",
    "🌊 Волны не спрашивают разрешения. Будь как волна — двигайся вперёд!",
    "🔑 Ключ к успеху — делать то, что другие откладывают на завтра!",
    "🌅 Каждый рассвет говорит: у тебя есть ещё один шанс. Не упусти!",
    "💫 Верь в себя даже когда никто другой не верит. Ты знаешь себя лучше!",
    "🎯 Маленький прогресс каждый день — огромный результат через год!",
    "🔥 Не жди подходящего момента — создай его сам!",
    "🌍 Мир принадлежит тем, кто встаёт рано и действует смело!",
    "💪 Твои руки, твой мозг, твоя воля — это всё что нужно для успеха!",
    "🏃 Начни сейчас, усовершенствуй по пути. Главное — начать!",
    "✨ Ты сильнее, чем думаешь. Умнее, чем кажется. Способнее, чем веришь!",
    "🎪 Жизнь слишком коротка для скуки — наполни её смыслом!",
    "🦅 Орлы не летают в стаях. Поднимись выше — туда, где твоё место!",
    "💰 Инвестируй в себя — это самый выгодный вклад в твоей жизни!",
    "🎭 Каждый день — это новая страница твоей истории. Пиши её красиво!",
    "🌻 Поворачивайся к солнцу — тени останутся позади!",
    "🏋️ Характер строится не в комфорте, а в преодолении. Преодолевай!",
]


def get_daily_motivation(days: int) -> str:
    return MOTIVATIONS[days % len(MOTIVATIONS)]


def build_daily_message(birthday_str: str) -> str:
    days = days_lived(birthday_str)
    years, days_since_bday = get_age(birthday_str)
    days_left = days_to_next_year(birthday_str)
    motivation = get_daily_motivation(days)
    today = datetime.now(BISHKEK_TZ).strftime("%d.%m.%Y")

    return (
        f"🌅 *Доброе утро!*\n\n"
        f"📅 Сегодня: *{today}*\n\n"
        f"🎂 Тебе *{years} лет* и *{days_since_bday} дней*\n"
        f"📆 До следующего дня рождения: *{days_left} дней*\n"
        f"🔢 Всего прожито: *{days:,} дней*\n\n"
        f"{motivation}\n\n"
        f"_Хорошего дня! Ты справишься со всем!_ 💫"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name or "друг"

    if chat_id in users:
        days = days_lived(users[chat_id])
        years, days_since = get_age(users[chat_id])
        await update.message.reply_text(
            f"👋 Привет, *{name}*! Ты уже зарегистрирован.\n\n"
            f"🎂 Тебе *{years} лет* и *{days_since} дней*\n"
            f"🔢 Прожито: *{days:,} дней*\n\n"
            f"Каждое утро в *8:00 по Бишкеку* жди моё сообщение!\n\n"
            f"/today — счёт прямо сейчас\n"
            f"/setbirthday — изменить дату рождения\n"
            f"/stop — отключить уведомления",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"👋 Привет, *{name}*! Я твой личный счётчик жизни!\n\n"
        f"Каждое утро в *8:00 по Бишкеку* я буду присылать тебе:\n\n"
        f"🎂 Сколько тебе лет и дней\n"
        f"📆 Сколько дней до следующего дня рождения\n"
        f"🔢 Сколько всего дней ты прожил\n"
        f"💪 Мотивацию на день — каждый день новую!\n\n"
        f"Введи свою дату рождения в формате:\n"
        f"*ДД.ММ.ГГГГ*\n\n"
        f"Например: `15.03.2005`",
        parse_mode="Markdown"
    )
    return WAITING_BIRTHDAY


async def set_birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 Введи новую дату рождения в формате:\n*ДД.ММ.ГГГГ*\n\nНапример: `15.03.2005`",
        parse_mode="Markdown"
    )
    return WAITING_BIRTHDAY


async def receive_birthday(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name or "друг"

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
        years, days_since = get_age(text)
        days_left = days_to_next_year(text)

        await update.message.reply_text(
            f"✅ *Отлично, {name}! Всё сохранено!*\n\n"
            f"🎂 Тебе *{years} лет* и *{days_since} дней*\n"
            f"📆 До следующего дня рождения: *{days_left} дней*\n"
            f"🔢 Всего прожито: *{days:,} дней*\n\n"
            f"🌅 Каждый день в *8:00 по Бишкеку* я буду присылать тебе сообщение с мотивацией!\n\n"
            f"Команды:\n"
            f"/today — счёт прямо сейчас\n"
            f"/setbirthday — изменить дату рождения\n"
            f"/stop — отключить уведомления",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат!\n\nВведи в формате *ДД.ММ.ГГГГ*\nНапример: `15.03.2005`",
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
        await update.message.reply_text(
            "😔 Уведомления отключены.\n\nЧтобы снова включить — напиши /start"
        )
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
