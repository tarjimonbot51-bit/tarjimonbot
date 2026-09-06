from __future__ import annotations

from html import escape

from config import LANGUAGES


def language_label(code: str | None) -> str:
    if code == "auto":
        return "🤖 Avtomatik aniqlash"
    language = LANGUAGES.get(code or "")
    return f"{language['flag']} {language['name']}" if language else "Noma'lum til"


def language_short_label(code: str | None) -> str:
    if code == "auto":
        return "Avtomatik"
    language = LANGUAGES.get(code or "")
    return f"{language['flag']} {language['name']}" if language else "Noma'lum"


def truncate_text(text: str, length: int = 160) -> str:
    clean = text.replace("\n", " ").strip()
    return clean if len(clean) <= length else clean[: length - 1] + "…"


def safe_html(text: str) -> str:
    return escape(text, quote=False)


def is_admin(user_id: int, admin_id: int) -> bool:
    return user_id == admin_id
