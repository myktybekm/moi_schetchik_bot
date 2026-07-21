import os
import logging
import sqlite3
from datetime import datetime, date, time
from html import escape
from zoneinfo import ZoneInfo

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    filters,
)

BOT_TOKEN = os.environ["BOT_TOKEN"]
BISHKEK_TZ = ZoneInfo("Asia/Bishkek")
WAITING_BIRTHDAY = 1
DB_FILE = "users.db"

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# =========================
# GTIN-ДАННЫЕ ИЗ EXCEL
# =========================

GTIN_DATA = {
    "А-072 Синий": {
        "S (48)": "04700087620011",
        "M (50)": "04700087620028",
        "L (52)": "04700087620035",
        "XL (54)": "04700087620042",
        "2XL (56)": "04700087620059",
        "3XL (58)": "04700087620066",
        "4XL (60)": "04700087620219",
        "5XL (62)": "04700087620226",
        "6XL (64)": "04700087621148",
    },
    "А-072 Черный": {
        "S (48)": "04700087620134",
        "M (50)": "04700087620141",
        "L (52)": "04700087620158",
        "XL (54)": "04700087620165",
        "2XL (56)": "04700087620172",
        "3XL (58)": "04700087620189",
        "4XL (60)": "04700087620370",
        "5XL (62)": "04700087620387",
        "6XL (64)": "04700087621155",
    },
    "А-105 Синий": {
        "S (48)": "04700087620714",
        "M (50)": "04700087620721",
        "L (52)": "04700087620738",
        "XL (54)": "04700087620745",
        "2XL (56)": "04700087620752",
        "3XL (58)": "04700087620769",
        "4XL (60)": "04700087620776",
        "5XL (62)": "04700087620783",
        "6XL (64)": "04700087621162",
    },
    "А-105 Черный": {
        "S (48)": "04700087620790",
        "M (50)": "04700087620806",
        "L (52)": "04700087620813",
        "XL (54)": "04700087620820",
        "2XL (56)": "04700087620837",
        "3XL (58)": "04700087620844",
        "4XL (60)": "04700087620851",
        "5XL (62)": "04700087620868",
        "6XL (64)": "04700087621179",
    },
    "А-106 Бордовый": {
        "S (48)": "04700087620875",
        "M (50)": "04700087620882",
        "L (52)": "04700087620899",
        "XL (54)": "04700087620905",
        "2XL (56)": "04700087620912",
        "3XL (58)": "04700087620929",
        "4XL (60)": "04700087620936",
        "5XL (62)": "04700087620943",
        "6XL (64)": "04700087621193",
    },
    "А-122 Синий": {
        "S (48)": "04700087621209",
        "M (50)": "04700087621216",
        "L (52)": "04700087621223",
        "XL (54)": "04700087621230",
        "2XL (56)": "04700087621247",
        "3XL (58)": "04700087621254",
        "4XL (60)": "04700087621261",
        "5XL (62)": "04700087621278",
        "6XL (64)": "04700087621285",
    },
    "А-122 Черный": {
        "S (48)": "04700087621292",
        "M (50)": "04700087621308",
        "L (52)": "04700087621315",
        "XL (54)": "04700087621322",
        "2XL (56)": "04700087621339",
        "3XL (58)": "04700087621346",
        "4XL (60)": "04700087621353",
        "5XL (62)": "04700087621360",
        "6XL (64)": "04700087621377",
    },
    "А-076 Бежевый": {
        "S (48)": "04700087620950",
        "M (50)": "04700087620967",
        "L (52)": "04700087620974",
        "XL (54)": "04700087620981",
        "2XL (56)": "04700087620998",
        "3XL (58)": "04700087621001",
        "4XL (60)": "04700087621018",
        "5XL (62)": "04700087621025",
        "6XL (64)": "04700087621384",
    },
    "Рубашка Белый": {
        "46": "04706627500850",
        "S (48)": "04706627500867",
        "M (50)": "04706627500874",
        "L (52)": "04706627500881",
        "XL (54)": "04706627500898",
        "2XL (56)": "04706627500904",
        "3XL (58)": "04706627500911",
        "4XL (60)": "04706627501062",
    },
    "Рубашка Черный": {
        "46": "04706627500928",
        "S (48)": "04706627500935",
        "M (50)": "04706627500942",
        "L (52)": "04706627500959",
        "XL (54)": "04706627500966",
        "2XL (56)": "04706627500973",
        "3XL (58)": "04706627500980",
        "4XL (60)": "04706627501079",
    },
    "Рубашка Темно-синий": {
        "44": "04706627501093",
        "46": "04706627501109",
        "S (48)": "04706627501116",
        "M (50)": "04706627501123",
        "L (52)": "04706627501130",
        "XL (54)": "04706627501147",
        "2XL (56)": "04706627501154",
    },
    "Рубашка Голубой": {
        "46": "04706627500997",
        "S (48)": "04706627501000",
        "M (50)": "04706627501017",
        "L (52)": "04706627501024",
        "XL (54)": "04706627501031",
        "2XL (56)": "04706627501048",
        "3XL (58)": "04706627501055",
        "4XL (60)": "04706627501086",
    },
}

MODEL_NAMES = list(GTIN_DATA.keys())


# =========================
# КЛАВИАТУРЫ
# =========================

def main_keyboard():
    return ReplyKeyboardMarkup(
        [["📦 GTIN коды"], ["📅 Сегодня", "⚙️ Изменить дату"]],
        resize_keyboard=True,
    )


def models_keyboard():
    rows = []
    for index, model_name in enumerate(MODEL_NAMES):
        rows.append([
            InlineKeyboardButton(
                model_name,
                callback_data=f"gtin_model:{index}",
            )
        ])

    return InlineKeyboardMarkup(rows)


# =========================
# БАЗА ПОЛЬЗОВАТЕЛЕЙ
# =========================

def create_database():
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                chat_id INTEGER PRIMARY KEY,
                birthday TEXT NOT NULL
            )
            """
        )


def save_user(chat_id, birthday):
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute(
            """
            INSERT OR REPLACE INTO users (chat_id, birthday)
            VALUES (?, ?)
            """,
            (chat_id, birthday),
        )


def get_user_birthday(chat_id):
    with sqlite3.connect(DB_FILE) as connection:
        result = connection.execute(
            "SELECT birthday FROM users WHERE chat_id = ?",
            (chat_id,),
        ).fetchone()

    return result[0] if result else None


def delete_user(chat_id):
    with sqlite3.connect(DB_FILE) as connection:
        connection.execute(
            "DELETE FROM users WHERE chat_id = ?",
            (chat_id,),
        )


def get_all_users():
    with sqlite3.connect(DB_FILE) as connection:
        return connection.execute(
            "SELECT chat_id, birthday FROM users"
        ).fetchall()


# =========================
# РАСЧЁТ ДАТ
# =========================

def today_bishkek():
    return datetime.now(BISHKEK_TZ).date()


def parse_birthday(birthday_str):
    return datetime.strptime(birthday_str, "%d.%m.%Y").date()


def birthday_for_year(birthday, year):
    try:
        return birthday.replace(year=year)
    except ValueError:
        return date(year, 2, 28)


def days_lived(birthday_str):
    birthday = parse_birthday(birthday_str)
    return (today_bishkek() - birthday).days


def days_to_next_birthday(birthday_str):
    birthday = parse_birthday(birthday_str)
    today = today_bishkek()

    next_birthday = birthday_for_year(birthday, today.year)

    if next_birthday <= today:
        next_birthday = birthday_for_year(birthday, today.year + 1)

    return (next_birthday - today).days


def get_age(birthday_str):
    birthday = parse_birthday(birthday_str)
    today = today_bishkek()

    years = today.year - birthday.year
    birthday_this_year = birthday_for_year(birthday, today.year)

    if today < birthday_this_year:
        years -= 1
        last_birthday = birthday_for_year(birthday, today.year - 1)
    else:
        last_birthday = birthday_this_year

    days_since = (today - last_birthday).days
    return years, days_since


MOTIVATIONS = [
    "💪 Каждый день — это новый шанс стать лучше. Используй его!",
    "🔥 Ты уже столько прошёл — не останавливайся сейчас!",
    "🌟 Великие дела начинаются с маленьких шагов.",
    "🚀 Твоё будущее создаётся прямо сейчас. Действуй!",
    "⚡ Энергия, фокус, результат — сегодня твой день!",
    "🎯 Маленький прогресс каждый день даёт большой результат.",
    "🌈 После любой бури приходит солнце.",
    "💡 Чему новому ты научишься сегодня?",
    "🏆 Победители продолжают действовать.",
    "🌱 Становись лучше хотя бы на 1% каждый день.",
]


def get_motivation(days):
    return MOTIVATIONS[days % len(MOTIVATIONS)]


def build_daily_message(birthday_str):
    days = days_lived(birthday_str)
    years, days_since = get_age(birthday_str)
    days_left = days_to_next_birthday(birthday_str)
    today = datetime.now(BISHKEK_TZ).strftime("%d.%m.%Y")

    return (
        "🌅 <b>Доброе утро!</b>\n\n"
        f"📅 Сегодня: <b>{today}</b>\n\n"
        f"🎂 Тебе <b>{years} лет и {days_since} дней</b>\n"
        f"🔢 Всего прожито: <b>{days:,} дней</b>\n"
        f"📆 До дня рождения: <b>{days_left} дней</b>\n\n"
        f"{get_motivation(days)}\n\n"
        "<i>Хорошего дня!</i>"
    )


# =========================
# GTIN-МЕНЮ
# =========================

async def gtin_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📦 Выбери модель:",
        reply_markup=models_keyboard(),
    )


async def gtin_model_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    try:
        index = int(query.data.split(":")[1])
        model_name = MODEL_NAMES[index]
    except (ValueError, IndexError):
        await query.edit_message_text("Ошибка выбора модели.")
        return

    lines = [f"📦 <b>{model_name}</b>\n"]

    for size_name, gtin in GTIN_DATA[model_name].items():
        lines.append(
            f"<b>{size_name}</b> — <code>{gtin}</code>"
        )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="gtin_back",
            )
        ]
    ])

    await query.edit_message_text(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def gtin_back_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "📦 Выбери модель:",
        reply_markup=models_keyboard(),
    )


# =========================
# КОМАНДЫ БОТА
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    name = escape(update.effective_user.first_name or "друг")
    birthday_str = get_user_birthday(chat_id)

    if birthday_str:
        days = days_lived(birthday_str)
        years, days_since = get_age(birthday_str)
        days_left = days_to_next_birthday(birthday_str)

        await update.message.reply_text(
            f"👋 Привет, {name}!\n\n"
            "Ты уже зарегистрирован ✅\n\n"
            f"🎂 Тебе <b>{years} лет и {days_since} дней</b>\n"
            f"🔢 Прожито: <b>{days:,} дней</b>\n"
            f"📆 До дня рождения: <b>{days_left} дней</b>\n\n"
            "⏰ Сообщение приходит каждый день в 08:00 по Бишкеку.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        f"👋 Привет, {name}!\n\n"
        "Я покажу твой возраст, прожитые дни и GTIN-коды товаров.\n\n"
        "📅 Напиши дату рождения:\n"
        "<b>ДД.ММ.ГГГГ</b>\n\n"
        "Например: <code>12.12.2004</code>",
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )

    return WAITING_BIRTHDAY


async def set_birthday_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "📅 Напиши дату рождения:\n\n"
        "<b>ДД.ММ.ГГГГ</b>\n\n"
        "Например: <code>12.12.2004</code>",
        parse_mode="HTML",
    )

    return WAITING_BIRTHDAY


async def receive_birthday(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    birthday_text = update.message.text.strip()
    chat_id = update.effective_chat.id
    name = escape(update.effective_user.first_name or "друг")

    try:
        birthday = parse_birthday(birthday_text)
        today = today_bishkek()

        if birthday > today:
            await update.message.reply_text(
                "❌ Дата рождения не может быть в будущем."
            )
            return WAITING_BIRTHDAY

        if (today - birthday).days > 36525:
            await update.message.reply_text(
                "❌ Возраст не может быть больше 100 лет."
            )
            return WAITING_BIRTHDAY

        save_user(chat_id, birthday_text)

        days = days_lived(birthday_text)
        years, days_since = get_age(birthday_text)
        days_left = days_to_next_birthday(birthday_text)

        await update.message.reply_text(
            f"✅ Готово, {name}!\n\n"
            f"🎂 Тебе <b>{years} лет и {days_since} дней</b>\n"
            f"🔢 Прожито: <b>{days:,} дней</b>\n"
            f"📆 До дня рождения: <b>{days_left} дней</b>\n\n"
            "⏰ Каждый день в 08:00 по Бишкеку я пришлю сообщение.",
            parse_mode="HTML",
            reply_markup=main_keyboard(),
        )

        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text(
            "❌ Неверная дата.\n\n"
            "Напиши так: <code>12.12.2004</code>",
            parse_mode="HTML",
        )
        return WAITING_BIRTHDAY


async def today_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    birthday_str = get_user_birthday(update.effective_chat.id)

    if not birthday_str:
        await update.message.reply_text(
            "❗ Сначала нажми /start"
        )
        return

    await update.message.reply_text(
        build_daily_message(birthday_str),
        parse_mode="HTML",
        reply_markup=main_keyboard(),
    )


async def stop_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    chat_id = update.effective_chat.id
    birthday_str = get_user_birthday(chat_id)

    if birthday_str:
        delete_user(chat_id)
        await update.message.reply_text(
            "Уведомления отключены.\n\n"
            "Чтобы включить снова, нажми /start"
        )
    else:
        await update.message.reply_text(
            "Ты ещё не зарегистрирован.\n\nНажми /start"
        )


async def cancel(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "Отменено. Нажми /start, чтобы начать снова."
    )
    return ConversationHandler.END


async def send_daily_messages(
    context: ContextTypes.DEFAULT_TYPE,
):
    for chat_id, birthday_str in get_all_users():
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=build_daily_message(birthday_str),
                parse_mode="HTML",
                reply_markup=main_keyboard(),
            )
        except Exception:
            logger.exception(
                "Не удалось отправить сообщение пользователю %s",
                chat_id,
            )


async def error_handler(update, context):
    logger.exception(
        "Ошибка при обработке сообщения",
        exc_info=context.error,
    )


def main():
    create_database()

    app = Application.builder().token(BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CommandHandler("setbirthday", set_birthday_command),
            MessageHandler(
                filters.Regex(r"^⚙️ Изменить дату$"),
                set_birthday_command,
            ),
        ],
        states={
            WAITING_BIRTHDAY: [
                MessageHandler(
                    filters.TEXT
                    & ~filters.COMMAND
                    & ~filters.Regex(r"^📦 GTIN коды$"),
                    receive_birthday,
                )
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel)
        ],
    )

    app.add_handler(conversation_handler)

    app.add_handler(CommandHandler("today", today_command))
    app.add_handler(CommandHandler("stop", stop_command))

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📅 Сегодня$"),
            today_command,
        )
    )

    app.add_handler(
        MessageHandler(
            filters.Regex(r"^📦 GTIN коды$"),
            gtin_menu,
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            gtin_model_callback,
            pattern=r"^gtin_model:",
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            gtin_back_callback,
            pattern=r"^gtin_back$",
        )
    )

    app.add_error_handler(error_handler)

    if app.job_queue is None:
        raise RuntimeError(
            "Добавь python-telegram-bot[job-queue] "
            "в requirements.txt"
        )

    app.job_queue.run_daily(
        send_daily_messages,
        time=time(
            hour=8,
            minute=0,
            tzinfo=BISHKEK_TZ,
        ),
        name="daily_message",
    )

    logger.info("Бот запущен")

    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
