from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import LANGUAGES
from database import Database
from keyboards.languages import source_languages, target_languages
from keyboards.main import main_menu
from utils.helpers import language_label


def create_router(db: Database) -> Router:
    router = Router(name="language")

    async def show_source(message: Message) -> None:
        await message.answer("🔄 Qaysi tildan tarjima qilamiz?", reply_markup=source_languages())

    @router.message(Command("language"))
    @router.message(F.text == "🔄 Tilni tanlash")
    async def language_start(message: Message) -> None:
        await show_source(message)

    @router.callback_query(F.data.startswith("lang_source:"))
    async def source_selected(callback: CallbackQuery, state: FSMContext) -> None:
        code = callback.data.split(":", 1)[1]
        if code != "auto" and code not in LANGUAGES:
            await callback.answer("Noto‘g‘ri til", show_alert=True)
            return
        await state.update_data(selected_source=code)
        await callback.answer()
        await callback.message.edit_text("🎯 Qaysi tilga tarjima qilamiz?", reply_markup=target_languages())

    @router.callback_query(F.data.startswith("lang_target:"))
    async def target_selected(callback: CallbackQuery, state: FSMContext) -> None:
        code = callback.data.split(":", 1)[1]
        if code not in LANGUAGES:
            await callback.answer("Noto‘g‘ri til", show_alert=True)
            return
        data = await state.get_data()
        source = data.get("selected_source")
        if not source:
            await callback.answer("Bu tanlov muddati tugagan", show_alert=True)
            return
        if source != "auto" and source == code:
            await callback.answer("Manba va target tili bir xil bo‘lishi mumkin emas", show_alert=True)
            return
        await db.update_languages(callback.from_user.id, source, code)
        await state.clear()
        await callback.answer("Til yo‘nalishi saqlandi")
        await callback.message.edit_text(
            f"✅ Tarjima yo‘nalishi saqlandi!\n\n🔄 {language_label(source)} → {language_label(code)}"
        )
        await callback.message.answer("Asosiy menyu:", reply_markup=main_menu())

    @router.callback_query(F.data == "language_back")
    async def language_back(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.answer()
        await callback.message.delete()
        await callback.message.answer("Asosiy menyu:", reply_markup=main_menu())

    return router
