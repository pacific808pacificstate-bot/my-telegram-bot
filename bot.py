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

# ... (весь код из предыдущего сообщения)
# [Здесь должен быть полный код бота]