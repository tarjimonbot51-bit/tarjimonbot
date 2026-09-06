from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

LANGUAGES = {
    "uz": {"name": "O'zbek", "flag": "🇺🇿", "api_code": "uz"},
    "ru": {"name": "Rus", "flag": "🇷🇺", "api_code": "ru"},
    "en": {"name": "Ingliz", "flag": "🇬🇧", "api_code": "en"},
    "tr": {"name": "Turk", "flag": "🇹🇷", "api_code": "tr"},
    "ar": {"name": "Arab", "flag": "🇸🇦", "api_code": "ar"},
    "de": {"name": "Nemis", "flag": "🇩🇪", "api_code": "de"},
    "fr": {"name": "Fransuz", "flag": "🇫🇷", "api_code": "fr"},
    "es": {"name": "Ispan", "flag": "🇪🇸", "api_code": "es"},
    "it": {"name": "Italyan", "flag": "🇮🇹", "api_code": "it"},
    "zh": {"name": "Xitoy", "flag": "🇨🇳", "api_code": "zh"},
    "ja": {"name": "Yapon", "flag": "🇯🇵", "api_code": "ja"},
    "ko": {"name": "Koreys", "flag": "🇰🇷", "api_code": "ko"},
}
MAX_TEXT_LENGTH = 4000
HISTORY_PAGE_SIZE = 5


@dataclass(frozen=True)
class Settings:
    bot_token: str
    admin_id: int
    translation_api_key: str | None
    translation_api_url: str
    database_path: str
    api_timeout: float


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "").strip()
    if not token or token == "YOUR_BOT_TOKEN":
        raise ValueError("BOT_TOKEN is not configured in .env")

    raw_admin_id = os.getenv("ADMIN_ID", "").strip()
    if not raw_admin_id or raw_admin_id == "YOUR_TELEGRAM_ID":
        raise ValueError("ADMIN_ID is not configured in .env")
    try:
        admin_id = int(raw_admin_id)
    except ValueError as exc:
        raise ValueError("ADMIN_ID must be an integer") from exc

    try:
        timeout = float(os.getenv("API_TIMEOUT", "12"))
    except ValueError as exc:
        raise ValueError("API_TIMEOUT must be a number") from exc
    if timeout <= 0:
        raise ValueError("API_TIMEOUT must be greater than zero")

    return Settings(
        bot_token=token,
        admin_id=admin_id,
        translation_api_key=os.getenv("TRANSLATION_API_KEY", "").strip() or None,
        translation_api_url=os.getenv("TRANSLATION_API_URL", "https://api.mymemory.translated.net").rstrip("/"),
        database_path=os.getenv("DATABASE_PATH", "translator_bot.db"),
        api_timeout=timeout,
    )
