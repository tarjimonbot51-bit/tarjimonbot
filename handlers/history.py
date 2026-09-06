from aiogram import F, Router
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import HISTORY_PAGE_SIZE
from database import Database
from keyboards.main import main_menu
from utils.helpers import language_short_label, safe_html, truncate_text


def create_router(db: Database) -> Router:
    router = Router(name="history")

    def controls(page: int, total_pages: int) -> InlineKeyboardMarkup:
        builder = InlineKeyboardBuilder()
        if page > 0:
            builder.button(text="⬅️ Oldingi", callback_data=f"history:{page - 1}")
        builder.button(text=f"{page + 1}/{total_pages}", callback_data="history_noop")
        if page + 1 < total_pages:
            builder.button(text="Keyingi ➡️", callback_data=f"history:{page + 1}")
        builder.adjust(3)
        return builder.as_markup()

    async def render(user_id: int, page: int) -> tuple[str, InlineKeyboardMarkup | None]:
        total = await db.count_user_history(user_id)
        if not total:
            return "📖 Hozircha tarjimalar tarixi mavjud emas.\n\n🌐 Birinchi tarjimangizni hoziroq qiling!", None
        total_pages = (total + HISTORY_PAGE_SIZE - 1) // HISTORY_PAGE_SIZE
        page = max(0, min(page, total_pages - 1))
        rows = await db.get_history(user_id, HISTORY_PAGE_SIZE, page * HISTORY_PAGE_SIZE)
        lines = ["📖 <b>Tarjimalar tarixi</b>\n"]
        for index, row in enumerate(rows, page * HISTORY_PAGE_SIZE + 1):
            lines.append(
                f"{index}. {safe_html(language_short_label(row['source_language']))} → "
                f"{safe_html(language_short_label(row['target_language']))}\n"
                f"{safe_html(truncate_text(row['source_text']))} → {safe_html(truncate_text(row['translated_text']))}\n"
            )
        return "\n".join(lines), controls(page, total_pages)

    @router.message(F.text == "📖 Tarjimalar tarixi")
    async def history_message(message: Message) -> None:
        text, markup = await render(message.from_user.id, 0)
        await message.answer(text, reply_markup=markup, parse_mode="HTML")

    @router.callback_query(F.data.startswith("history:"))
    async def history_page(callback: CallbackQuery) -> None:
        try:
            page = int(callback.data.split(":", 1)[1])
        except (ValueError, IndexError):
            await callback.answer("Noto‘g‘ri sahifa", show_alert=True)
            return
        text, markup = await render(callback.from_user.id, page)
        await callback.answer()
        await callback.message.edit_text(text, reply_markup=markup, parse_mode="HTML")

    @router.callback_query(F.data == "history_noop")
    async def history_noop(callback: CallbackQuery) -> None:
        await callback.answer()

    @router.message(F.text == "ℹ️ Bot haqida")
    async def about_handler(message: Message) -> None:
        await message.answer(
            "🌐 Translator Bot\n\n⚡ Tezkor tarjima\n🌍 Ko‘p tillarni qo‘llab-quvvatlash\n"
            "📖 Tarjima tarixini saqlash\n🤖 Qulay Telegram interfeysi",
            reply_markup=main_menu(),
        )

    return router
