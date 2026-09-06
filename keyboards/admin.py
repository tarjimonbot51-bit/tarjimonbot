from aiogram.types import InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="👥 Foydalanuvchilar", callback_data="admin_users")
    builder.button(text="📊 Statistika", callback_data="admin_stats")
    builder.button(text="📢 Reklama yuborish", callback_data="admin_broadcast")
    builder.adjust(1)
    return builder.as_markup()


def broadcast_confirmation() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Ha", callback_data="broadcast_yes")
    builder.button(text="❌ Yo'q", callback_data="broadcast_no")
    builder.adjust(2)
    return builder.as_markup()
