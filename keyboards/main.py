from aiogram.types import KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def main_menu() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    for text in ("🌐 Tarjima qilish", "🔄 Tilni tanlash", "📖 Tarjimalar tarixi", "ℹ️ Bot haqida"):
        builder.add(KeyboardButton(text=text))
    builder.adjust(2, 2)
    return builder.as_markup(resize_keyboard=True)
