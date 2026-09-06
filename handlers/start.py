from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from config import Settings
from database import Database
from keyboards.admin import admin_menu
from keyboards.main import main_menu
from utils.helpers import is_admin


def create_router(db: Database, settings: Settings) -> Router:
    router = Router(name="start")

    @router.message(CommandStart())
    async def start_handler(message: Message) -> None:
        user = message.from_user
        await db.upsert_user(user.id, user.username, user.full_name)
        if is_admin(user.id, settings.admin_id):
            await message.answer(
                "👨‍💻 Admin panel\n\nKerakli bo‘limni tanlang:",
                reply_markup=admin_menu(),
            )
            return
        await message.answer(
            "👋 Assalomu alaykum!\n\n🌐 Translator Bot'ga xush kelibsiz!\n\n"
            "Men sizga matnlarni tez va qulay tarjima qilishga yordam beraman.\n\n"
            "Quyidagi menyudan foydalaning 👇",
            reply_markup=main_menu(),
        )

    @router.message(Command("help"))
    async def help_handler(message: Message) -> None:
        await message.answer(
            "📚 Botdan foydalanish:\n\n"
            "🌐 Tarjima qilish\n— Matn yuboring va tarjima qiling.\n\n"
            "🔄 Tilni tanlash\n— Manba va target tillarni belgilang.\n\n"
            "📖 Tarjimalar tarixi\n— Oldingi tarjimalaringizni ko‘ring.\n\n"
            "ℹ️ Bot haqida\n— Bot haqida ma’lumot.\n\n"
            "/language — til sozlamalarini ochish.\n\n"
            "/cancel — joriy amalni bekor qilish."
        )

    return router
