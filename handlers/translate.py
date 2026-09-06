from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from config import LANGUAGES, MAX_TEXT_LENGTH
from database import Database
from keyboards.main import main_menu
from services.translator import TranslationServiceError, TranslatorService
from states.translation import TranslationStates
from utils.helpers import language_label, safe_html


def create_router(db: Database, translator: TranslatorService) -> Router:
    router = Router(name="translate")

    @router.message(Command("cancel"))
    async def cancel_handler(message: Message, state: FSMContext) -> None:
        await state.clear()
        await message.answer("❌ Amal bekor qilindi.\n\nAsosiy menyudan kerakli bo‘limni tanlang.", reply_markup=main_menu())

    @router.message(F.text == "🌐 Tarjima qilish")
    async def translation_start(message: Message, state: FSMContext) -> None:
        await state.set_state(TranslationStates.waiting_for_text)
        await message.answer("📝 Tarjima qilmoqchi bo‘lgan matningizni yuboring.\n\n💡 Bekor qilish uchun /cancel yuboring.")

    @router.message(TranslationStates.waiting_for_text, F.text)
    async def translate_message(message: Message, state: FSMContext) -> None:
        text = message.text.strip()
        if not text:
            await message.answer("⚠️ Iltimos, tarjima qilish uchun matn yuboring.")
            return
        if len(text) > MAX_TEXT_LENGTH:
            await message.answer("⚠️ Matn juda uzun.\n\nIltimos, matnni qisqaroq qismlarga bo‘lib yuboring.")
            return

        user = await db.get_user(message.from_user.id)
        if not user:
            await db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
            user = await db.get_user(message.from_user.id)
        source = user["selected_source_language"]
        target = user["selected_target_language"]
        if source != "auto" and source == target:
            await message.answer("ℹ️ Manba va tarjima tili bir xil. Iltimos, boshqa target tilni tanlang.")
            return

        progress = await message.answer("⏳ Tarjima qilinmoqda...")
        try:
            result = await translator.translate_text(text, source, target)
        except TranslationServiceError:
            await progress.edit_text("⚠️ Hozir tarjima xizmatida vaqtinchalik muammo yuz berdi.\n\nIltimos, birozdan keyin qayta urinib ko‘ring.")
            return

        actual_source = result.detected_language or source
        await db.save_translation(message.from_user.id, actual_source, target, text, result.translated_text)
        await state.clear()
        await progress.edit_text(
            f"🌐 <b>Tarjima:</b>\n\n{safe_html(result.translated_text)}\n\n"
            f"🔄 {safe_html(language_label(actual_source))} → {safe_html(language_label(target))}",
            parse_mode="HTML",
        )

    @router.message(TranslationStates.waiting_for_text)
    async def unsupported_translation_message(message: Message) -> None:
        await message.answer("⚠️ Iltimos, matn ko‘rinishidagi xabar yuboring.")

    return router
