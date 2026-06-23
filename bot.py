import logging
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

BOT_TOKEN = "8959341115:AAFqmyHEwdWOvr8CQySjrHvzJMYSd5dGhEA"
BISHKEK_TZ = ZoneInfo("Asia/Bishkek")
WAITING_BIRTHDAY = 1

users = {}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def days_lived(birthday_str):
    birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()
    return (date.today() - birthday).days


def days_to_next_birthday(birthday_str):
    birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()
    today = date.today()
    next_bd = birthday.replace(year=today.year)
    if next_bd <= today:
        next_bd = next_bd.replace(year=today.year + 1)
    return (next_bd - today).days


def get_age(birthday_str):
    birthday = datetime.strptime(birthday_str, "%d.%m.%Y").date()
    today = date.today()
    years = today.year - birthday.year
    last_bd = birthday.replace(year=today.year)
    if last_bd > today:
        years -= 1
        last_bd = birthday.replace(year=today.year - 1)
    days_since = (today - last_bd).days
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
    "🏆 Победители делают выбор каждое утро. Ты выбираешь победу?",
    "🌱 Расти каждый день — даже на 1% лучше!",
    "💎 Алмаз — это уголь, который выдержал давление. Держись!",
    "🦁 Просыпайся как лев — голодный до успеха!",
    "⭐ Твои мечты не случайны — они даны тебе не зря!",
    "🌊 Двигайся вперёд — как волна, которую не остановить!",
    "🔑 Ключ к успеху — делать то, что другие откладывают!",
    "🌅 Каждый рассвет говорит: у тебя есть ещё один шанс!",
    "💫 Верь в себя даже когда никто другой не верит!",
    "🌍 Мир принадлежит тем, кто действует смело!",
    "🏃 Начни сейчас, усовершенствуй по пути!",
    "✨ Ты сильнее, умнее и способнее, чем думаешь!",
    "🎪 Жизнь слишком коротка — наполни её смыслом!",
    "🦅 Поднимись выше — туда, где твоё место!",
    "💰 Инвестируй в себя — это самый выгодный вклад!",
    "🎭 Каждый день — новая страница твоей истории!",
    "🌻 Поворачивайся к солнцу — тени останутся позади!",
    "🏋️ Характер строится не в комфорте, а в преодолении!",
    "🎸 Живи так, чтобы было что вспомнить!",
    "🔥 Не жди подходящего момента — создай его сам!",
    "🌙 Даже луна проходит через тёмные ночи, но всегда светит снова!",
    "🎯 Маленький прогресс каждый день — огромный результат через год!",
]


def get_motivation(days):
    return MOTIVATIONS[days % len(MOTIVATIONS)]


def build_daily_message(birthday_str):
    days = days_lived(birthday_str)
    years, days_since = get_age(birthday_str)
    days_left = days_to_next_birthday(birthday_str)
    motivation = get_motivation(days)
    today = datetime.now(BISHKEK_TZ).strftime("%d.%m.%Y")

    return (
        f"🌅 *Доброе утро!*\n\n"
        f"📅 Сегодня: *{today}*\n\n"
        f"🎂 Тебе *{years} лет* и *{days_since} дней*\n"
        f"🔢 Всего прожито: *{days:,} дней*\n"
        f"📆 До дня рождения: *{days_left} дней*\n\n"
        f"{motivation}\n\n"
        f"_Хорошего дня! Ты справишься! 💫_"
    )


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = update.effective_user.first_name or "друг"

    if chat_id in users:
        days = days_lived(users[chat_id])
        years, days_since = get_age(users[chat_id])
        days_left = days_to_next_birthday(users[chat_id])
        await update.message.reply_text(
            f"👋 Привет, {name}!\n\n"
            f"Ты уже зарегистрирован ✅\n\n"
            f"🎂 Тебе *{years} лет* и *{days_since} дней*\n"
            f"🔢 Прожито: *{days:,} дней*\n"
            f"📆 До дня рождения: *{days_left} дней*\n\n"
            f"Каждый день в *8:00 утра по Бишкеку* я пишу тебе 🌅\n\n"
            f"👉 /today — получить сообщение прямо сейчас\n"
            f"👉 /setbirthday — изменить дату рождения\n"
            f"👉 /stop — отключить уведомления",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    # Новый пользователь — рассказываем что умеем
    await update.message.reply_text(
        f"👋 Привет, {name}! Я твой личный счётчик жизни!\n\n"
        f"Вот что я умею:\n\n"
        f"🎂 Скажу сколько тебе лет и дней\n"
        f"🔢 Покажу сколько дней ты уже прожил\n"
        f"📆 Напомню сколько дней до твоего дня рождения\n"
        f"💪 Каждый день буду мотивировать тебя — каждый раз новые слова!\n\n"
        f"⏰ Каждое утро в *8:00 по Бишкеку* я буду писать тебе сам!\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📅 Напиши свою дату рождения в формате:\n\n"
        f"*ДД.ММ.ГГГГ*\n\n"
        f"Например: `12.12.2004`",
        parse_mode="Markdown"
    )
    return WAITING_BIRTHDAY


async def set_birthday_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"📅 Напиши свою дату рождения в формате:\n\n"
        f"*ДД.ММ.ГГГГ*\n\n"
        f"Например: `12.12.2004`",
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
            await update.message.reply_text(
                "❌ Дата рождения не может быть в будущем!\n\n"
                "Попробуй ещё раз, например: `12.12.2004`",
                parse_mode="Markdown"
            )
            return WAITING_BIRTHDAY

        if (date.today() - birthday).days > 365 * 100:
            await update.message.reply_text(
                "❌ Слишком старая дата. Попробуй ещё раз:"
            )
            return WAITING_BIRTHDAY

        users[chat_id] = text
        days = days_lived(text)
        years, days_since = get_age(text)
        days_left = days_to_next_birthday(text)

        await update.message.reply_text(
            f"✅ Отлично, {name}! Всё сохранил!\n\n"
            f"🎂 Тебе *{years} лет* и *{days_since} дней*\n"
            f"🔢 Всего прожито: *{days:,} дней*\n"
            f"📆 До дня рождения: *{days_left} дней*\n\n"
            f"⏰ Теперь каждый день в *8:00 утра по Бишкеку* я буду писать тебе!\n\n"
            f"Желаю удачи и жди уведомления! 🚀\n\n"
            f"👉 Хочешь увидеть прямо сейчас? Напиши /today",
            parse_mode="Markdown"
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            f"❌ Не понял дату!\n\n"
            f"Напиши в формате *ДД.ММ.ГГГГ*\n\n"
            f"Например: `12.12.2004`",
            parse_mode="Markdown"
        )
        return WAITING_BIRTHDAY


async def today_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id not in users:
        await update.message.reply_text(
            "❗ Сначала зарегистрируйся!\n\nНапиши /start"
        )
        return
    message = build_daily_message(users[chat_id])
    await update.message.reply_text(message, parse_mode="Markdown")


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if chat_id in users:
        del users[chat_id]
        await update.message.reply_text(
            "😔 Уведомления отключены.\n\n"
            "Чтобы снова включить — напиши /start"
        )
    else:
        await update.message.reply_text(
            "Ты ещё не зарегистрирован.\n\nНапиши /start"
        )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Отменено.\n\nНапиши /start чтобы начать заново."
    )
    return ConversationHandler.END


async def send_daily_messages(context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"Отправка утренних сообщений. Пользователей: {len(users)}")
    for chat_id, birthday_str in list(users.items()):
        try:
            message = build_daily_message(birthday_str)
            await context.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode="Markdown"
            )
            logger.info(f"Отправлено: {chat_id}")
        except Exception as e:
            logger.error(f"Ошибка {chat_id}: {e}")


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

    # 8:00 Бишкек = 02:00 UTC
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
