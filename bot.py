import logging
from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
)
from datetime import time, datetime, timedelta
import pytz
import random

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация (легко поменять под себя)
WAKE_UP_TIME, BEDTIME, DAY_REVIEW = range(3)
user_schedules = {}
user_data_store = {}  # Для хранения данных пользователя за день

# Ваше расписание по умолчанию (можно менять)
DEFAULT_SCHEDULE = {
    "6:30 - 6:40": "Подъем и стакан воды",
    "6:40 - 7:30": "Велопоездка",
    "7:30 - 8:05": "Душ, завтрак, планирование задач",
    "8:05 - 15:05": "Рабочий блок (7 часов)",
    "15:05 - 15:30": "Подведение итогов дня, план на завтра",
    "15:30 - 16:15": "Отдых, душ, переодевание",
    "16:15 - 17:30": "Время с семьей / приготовление еды",
    "17:30 - 19:00": "Семейный ужин",
    "19:00 - 22:00": "Качественное время с семьей",
    "22:00 - 22:30": "Подготовка к следующему дню",
    "22:30 - 23:00": "Чтение, медитация, расслабление",
}

# База мотивационных цитат
MOTIVATIONAL_QUOTES = [
    "Каждый продуктивный день начинается с правильного решения. Ты уже его принял(а)! 🚀",
    "Ты не procrastinator, ты doer! Просто иногда нужно напоминание. 😉",
    "Сосредоточься на одном деле. Потом на следующем. И так ты свернешь горы. ⛰️",
    "Даже самый длинный путь начинается с первого шага. Ты его уже сделал(а)! 👣",
    "Ты управляешь своим днем, а не день управляет тобой. 💪",
    "Успех — это сумма небольших усилий, повторяемых изо дня в день. Сегодня — очередной кирпичик в твоем успехе. 🧱",
]

GOOD_NIGHT_QUOTES = [
    "Сон — это суперсила продуктивных людей. Выспись хорошенько! 😴",
    "Завтра — новый день для новых свершений. Приятных снов! 🌙",
    "Ты сегодня хорошо потрудился(ась). Заслужил(а) отдых. Спокойной ночи! 💫",
]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /start - начало дня."""
    user_id = update.effective_user.id
    # Инициализируем расписание для пользователя
    user_schedules[user_id] = DEFAULT_SCHEDULE.copy()
    
    # Отправляем план на день
    schedule_text = "📅 <b>Твой план на сегодня:</b>\n\n"
    for time_slot, task in user_schedules[user_id].items():
        schedule_text += f"<b>{time_slot}</b>: {task}\n"
    
    # Добавляем мотивацию
    motivation = random.choice(MOTIVATIONAL_QUOTES)
    
    await update.message.reply_text(
        f"Доброе утро, {update.effective_user.first_name}! ☀️\n\n"
        f"{motivation}\n\n"
        f"{schedule_text}\n"
        "Во сколько ты планируешь лечь спать сегодня? (например, 23:00 или 23:30)",
        parse_mode='HTML'
    )
    
    return BEDTIME

async def set_bedtime(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатываем время отхода ко сну."""
    user_id = update.effective_user.id
    bedtime_text = update.message.text
    
    # Простая валидация времени
    try:
        if len(bedtime_text) == 5 and bedtime_text[2] == ':':
            hours = int(bedtime_text[:2])
            minutes = int(bedtime_text[3:])
            if 0 <= hours <= 23 and 0 <= minutes <= 59:
                # Сохраняем время сна
                if user_id not in user_data_store:
                    user_data_store[user_id] = {}
                user_data_store[user_id]['bedtime'] = bedtime_text
                
                # Рассчитываем время подъема (предполагаем 7.5 часов сна)
                bedtime = datetime.strptime(bedtime_text, "%H:%M")
                wakeup_time = (bedtime + timedelta(hours=7, minutes=30)).strftime("%H:%M")
                
                await update.message.reply_text(
                    f"⏰ Отлично! Записал твой отбой на {bedtime_text}. "
                    f"Идеальное время подъема: {wakeup_time}\n\n"
                    "Не забывай отмечать задачи командой /done по мере выполнения! "
                    "А вечером напиши /finish для подведения итогов дня.",
                    reply_markup=ReplyKeyboardRemove()
                )
                return ConversationHandler.END
    except ValueError:
        pass
    
    await update.message.reply_text(
        "Пожалуйста, введите время в формате ЧЧ:MM (например, 23:00 или 08:30)"
    )
    return BEDTIME

async def finish_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /finish - завершение дня."""
    user_id = update.effective_user.id
    
    await update.message.reply_text(
        "Молодец, что завершаешь день осознанно! 👍\n\n"
        "Как прошел твой день? Напиши пару предложений:\n"
        "• Что получилось хорошо?\n"
        "• Что можно улучшить завтра?\n\n"
        "Это поможет стать еще продуктивнее!"
    )
    
    return DAY_REVIEW

async def save_day_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняем итоги дня."""
    user_id = update.effective_user.id
    day_review = update.message.text
    
    # Сохраняем отчет
    if user_id not in user_data_store:
        user_data_store[user_id] = {}
    user_data_store[user_id]['last_review'] = day_review
    user_data_store[user_id]['review_date'] = datetime.now().strftime("%Y-%m-%d")
    
    # Отправляем прощальное сообщение
    good_night = random.choice(GOOD_NIGHT_QUOTES)
    bedtime = user_data_store[user_id].get('bedtime', '23:00')
    
    await update.message.reply_text(
        f"Спасибо за отчет! Ты большой(ая) молодец! 🙌\n\n"
        f"{good_night}\n\n"
        f"Твой отбой в {bedtime}. Приятных снов! 😴",
        reply_markup=ReplyKeyboardRemove()
    )
    
    return ConversationHandler.END

async def show_today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /today - показать расписание на сегодня."""
    user_id = update.effective_user.id
    schedule = user_schedules.get(user_id, DEFAULT_SCHEDULE)
    
    text = "📅 Ваше расписание на сегодня:\n\n"
    for time_slot, task in schedule.items():
        text += f"<b>{time_slot}</b>: {task}\n"
    
    await update.message.reply_text(text, parse_mode='HTML')

async def task_done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /done - отметить задачу как выполненную."""
    motivation = random.choice(MOTIVATIONAL_QUOTES)
    await update.message.reply_text(
        f"✅ Отлично! Вы молодец! Продолжайте в том же духе! 💪\n\n"
        f"{motivation}\n\n"
        "Что дальше?\n"
        "/today - Посмотреть расписание\n"
        "/next - Что делать сейчас?"
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена диалога."""
    await update.message.reply_text(
        'Диалог отменен. Используй /start чтобы начать день заново.',
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок."""
    logger.error(f"Update {update} caused error {context.error}")
    await update.message.reply_text("Произошла ошибка. Попробуйте еще раз.")

def main():
    """Запуск бота."""
    APPLICATION = ApplicationBuilder().token("7621410997:AAHwLB41A3FserXty1ashJ1zKfGnLy4I3K4").build()
    
    # Диалог для начала дня
    start_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            BEDTIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, set_bedtime)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Диалог для завершения дня
    finish_conv_handler = ConversationHandler(
        entry_points=[CommandHandler('finish', finish_day)],
        states={
            DAY_REVIEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_day_review)],
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Добавляем обработчики
    APPLICATION.add_handler(start_conv_handler)
    APPLICATION.add_handler(finish_conv_handler)
    APPLICATION.add_handler(CommandHandler("today", show_today))
    APPLICATION.add_handler(CommandHandler("done", task_done))
    
    # Запускаем бота
    APPLICATION.run_polling()
    print("Бот запущен!")

if __name__ == "__main__":
    main()
