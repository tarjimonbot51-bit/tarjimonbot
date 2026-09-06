from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import LANGUAGES


def source_languages() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🤖 Avtomatik aniqlash", callback_data="lang_source:auto")
    for code, language in LANGUAGES.items():
        builder.button(text=f"{language['flag']} {language['name']}", callback_data=f"lang_source:{code}")
    builder.button(text="🔙 Orqaga", callback_data="language_back")
    builder.adjust(2)
    return builder.as_markup()


def target_languages() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for code, language in LANGUAGES.items():
        builder.button(text=f"{language['flag']} {language['name']}", callback_data=f"lang_target:{code}")
    builder.button(text="🔙 Orqaga", callback_data="language_back")
    builder.adjust(2)
    return builder.as_markup()
