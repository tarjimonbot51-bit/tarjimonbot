from __future__ import annotations

import asyncio
import logging

from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import Settings
from database import Database
from keyboards.admin import admin_menu, broadcast_confirmation
from states.admin import AdminStates
from utils.helpers import is_admin

logger = logging.getLogger(__name__)


def create_router(db: Database, settings: Settings) -> Router:
    router = Router(name="admin")

    def allowed(user_id: int) -> bool:
        return is_admin(user_id, settings.admin_id)

    @router.message(Command("admin"))
    async def admin_handler(message: Message) -> None:
        if not allowed(message.from_user.id):
            await message.answer("⛔ Sizda admin paneldan foydalanish huquqi yo‘q.")
            return
        await message.answer("👨‍💻 Admin panel\n\nKerakli bo‘limni tanlang:", reply_markup=admin_menu())

    @router.callback_query(F.data == "admin_users")
    async def admin_users(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await callback.answer("Huquq yo‘q", show_alert=True)
            return
        await callback.answer()
        await callback.message.edit_text(f"👥 Jami foydalanuvchilar: {await db.count_users()}", reply_markup=admin_menu())

    @router.callback_query(F.data == "admin_stats")
    async def admin_stats(callback: CallbackQuery) -> None:
        if not allowed(callback.from_user.id):
            await callback.answer("Huquq yo‘q", show_alert=True)
            return
        await callback.answer()
        text = (
            "📊 <b>Bot statistikasi</b>\n\n"
            f"👥 Jami foydalanuvchilar: {await db.count_users()}\n"
            f"📅 Bugun qo‘shilganlar: {await db.count_today_users()}\n"
            f"🌐 Jami tarjimalar: {await db.count_translations()}"
        )
        await callback.message.edit_text(text, reply_markup=admin_menu(), parse_mode="HTML")

    @router.callback_query(F.data == "admin_broadcast")
    async def broadcast_start(callback: CallbackQuery, state: FSMContext) -> None:
        if not allowed(callback.from_user.id):
            await callback.answer("Huquq yo‘q", show_alert=True)
            return
        await state.set_state(AdminStates.waiting_for_broadcast)
        await callback.answer()
        await callback.message.answer("📢 Barcha foydalanuvchilarga yuboriladigan matnni yuboring.\n\nBekor qilish: /cancel")

    @router.message(AdminStates.waiting_for_broadcast, F.text)
    async def broadcast_text(message: Message, state: FSMContext) -> None:
        if not allowed(message.from_user.id):
            await state.clear()
            return
        await state.update_data(broadcast_type="text", broadcast_text=message.text)
        await state.set_state(AdminStates.confirming_broadcast)
        await message.answer(
            "📢 Ushbu xabar barcha foydalanuvchilarga yuborilsinmi?\n\n" + message.text,
            reply_markup=broadcast_confirmation(),
            parse_mode=None,
        )

    @router.message(AdminStates.waiting_for_broadcast, F.photo)
    async def broadcast_photo(message: Message, state: FSMContext) -> None:
        if not allowed(message.from_user.id):
            await state.clear()
            return
        photo_id = message.photo[-1].file_id
        caption = message.caption or ""
        await state.update_data(
            broadcast_type="photo",
            broadcast_photo_id=photo_id,
            broadcast_caption=caption,
        )
        await state.set_state(AdminStates.confirming_broadcast)
        await message.answer("📢 Ushbu rasm barcha foydalanuvchilarga yuborilsinmi?")
        await message.answer_photo(
            photo=photo_id,
            caption=caption or None,
            reply_markup=broadcast_confirmation(),
        )

    @router.callback_query(AdminStates.confirming_broadcast, F.data == "broadcast_no")
    async def broadcast_no(callback: CallbackQuery, state: FSMContext) -> None:
        await state.clear()
        await callback.answer("Bekor qilindi")
        await callback.message.edit_text("❌ Reklama bekor qilindi.", reply_markup=admin_menu())

    @router.callback_query(AdminStates.confirming_broadcast, F.data == "broadcast_yes")
    async def broadcast_yes(callback: CallbackQuery, state: FSMContext) -> None:
        if not allowed(callback.from_user.id):
            await callback.answer("Huquq yo‘q", show_alert=True)
            return
        data = await state.get_data()
        broadcast_type = data.get("broadcast_type")
        text = data.get("broadcast_text")
        photo_id = data.get("broadcast_photo_id")
        caption = data.get("broadcast_caption", "")
        await state.clear()
        if broadcast_type == "text" and not text:
            await callback.answer("Bu amal muddati tugagan", show_alert=True)
            return
        if broadcast_type == "photo" and not photo_id:
            await callback.answer("Bu amal muddati tugagan", show_alert=True)
            return
        if broadcast_type not in {"text", "photo"}:
            await callback.answer("Bu amal muddati tugagan", show_alert=True)
            return
        await callback.answer("Yuborish boshlandi")
        sent = failed = 0
        for user_id in await db.get_all_user_ids():
            try:
                if broadcast_type == "photo":
                    await callback.bot.send_photo(user_id, photo_id, caption=caption or None, parse_mode=None)
                else:
                    await callback.bot.send_message(user_id, text, parse_mode=None)
                sent += 1
                await asyncio.sleep(0.05)
            except TelegramRetryAfter as exc:
                await asyncio.sleep(exc.retry_after)
                try:
                    if broadcast_type == "photo":
                        await callback.bot.send_photo(user_id, photo_id, caption=caption or None, parse_mode=None)
                    else:
                        await callback.bot.send_message(user_id, text, parse_mode=None)
                    sent += 1
                except Exception:
                    failed += 1
            except (TelegramForbiddenError, TelegramNetworkError):
                failed += 1
            except Exception as exc:
                failed += 1
                logger.warning("Broadcast delivery failed for user %s: %s", user_id, exc)
        total = sent + failed
        result_text = (
            f"📢 Reklama yakunlandi.\n\n✅ Yuborildi: {sent}\n"
            f"❌ Yuborilmadi: {failed}\n👥 Jami: {total}"
        )
        try:
            await callback.message.edit_text(result_text, reply_markup=admin_menu())
        except TelegramBadRequest:
            await callback.message.answer(result_text, reply_markup=admin_menu())

    return router
