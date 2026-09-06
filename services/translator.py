from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass

import aiohttp

from config import LANGUAGES

logger = logging.getLogger(__name__)


class TranslationServiceError(Exception):
    pass


@dataclass(frozen=True)
class TranslationResult:
    translated_text: str
    detected_language: str | None = None


class TranslatorService:
    def __init__(self, api_url: str, api_key: str | None, timeout: float):
        self.api_url = api_url.rstrip("/")
        self.is_mymemory = "mymemory.translated.net" in self.api_url.lower()
        self.endpoint = f"{self.api_url}/translate"
        self.api_key = api_key
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.session: aiohttp.ClientSession | None = None
        self.cache: dict[tuple[str, str, str], TranslationResult] = {}

    async def start(self) -> None:
        self.session = aiohttp.ClientSession(timeout=self.timeout)

    async def close(self) -> None:
        if self.session and not self.session.closed:
            await self.session.close()

    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> TranslationResult:
        if source_lang != "auto" and source_lang == target_lang:
            return TranslationResult(text, source_lang)
        key = (text, source_lang, target_lang)
        if key in self.cache:
            return self.cache[key]
        if not self.session:
            raise TranslationServiceError("Translation service is not started")

        actual_source = source_lang
        if actual_source == "auto":
            actual_source = detect_language(text)
            if not actual_source:
                raise TranslationServiceError("Could not detect source language")

        for attempt in range(2):
            try:
                if self.is_mymemory:
                    source_code = LANGUAGES[actual_source]["api_code"]
                    target_code = LANGUAGES[target_lang]["api_code"]
                    params = {"q": text, "langpair": f"{source_code}|{target_code}"}
                    async with self.session.get(f"{self.api_url}/get", params=params) as response:
                        data = await self._read_response(response, attempt)
                else:
                    payload = {
                        "q": text,
                        "source": LANGUAGES[actual_source]["api_code"],
                        "target": LANGUAGES[target_lang]["api_code"],
                        "format": "text",
                    }
                    if self.api_key:
                        payload["api_key"] = self.api_key
                    async with self.session.post(self.endpoint, data=payload) as response:
                        data = await self._read_response(response, attempt)

                if self.is_mymemory:
                    response_data = data.get("responseData", {})
                    translated = str(response_data.get("translatedText", "")).strip()
                    if data.get("responseStatus") not in (200, "200") or not translated:
                        raise TranslationServiceError("Translation provider rejected the request")
                    result = TranslationResult(translated, actual_source)
                else:
                    translated = str(data.get("translatedText", "")).strip()
                    if not translated:
                        raise TranslationServiceError("API response did not contain translatedText")
                    detected = data.get("detectedLanguage")
                    if isinstance(detected, dict):
                        detected = detected.get("language")
                    result = TranslationResult(translated, self._normalize_detected(detected) or actual_source)
                self.cache[key] = result
                return result
            except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
                if attempt == 1:
                    logger.error("Translation API network error: %s", exc)
                    raise TranslationServiceError("Translation API network error") from exc
        raise TranslationServiceError("Translation API request failed")

    @staticmethod
    async def _read_response(response: aiohttp.ClientResponse, attempt: int) -> dict:
        if response.status >= 500 and attempt == 0:
            await asyncio.sleep(0.5)
            raise aiohttp.ClientError("Temporary translation server error")
        if response.status >= 400:
            detail = (await response.text())[:300]
            raise TranslationServiceError(f"API returned HTTP {response.status}: {detail}")
        try:
            return await response.json(content_type=None)
        except (ValueError, aiohttp.ContentTypeError) as exc:
            raise TranslationServiceError("Translation API returned invalid JSON") from exc

    @staticmethod
    def _normalize_detected(value: object) -> str | None:
        code = str(value).lower().split("-")[0] if value else ""
        return code if code in LANGUAGES else None


def detect_language(text: str) -> str | None:
    """Detect common scripts locally before sending a request to a provider."""
    if any("\u0400" <= char <= "\u04ff" for char in text):
        return "ru"
    if any("\u0600" <= char <= "\u06ff" for char in text):
        return "ar"
    if any("\u3040" <= char <= "\u30ff" for char in text):
        return "ja"
    if any("\uac00" <= char <= "\ud7af" for char in text):
        return "ko"
    if any("\u4e00" <= char <= "\u9fff" for char in text):
        return "zh"
    words = set(re.findall(r"[a-zA-Z'ʻ‘’]+", text.lower()))
    if words.intersection(("salom", "qanday", "uchun", "men", "siz")):
        return "uz"
    if words.intersection(("hola", "gracias", "como")):
        return "es"
    if words.intersection(("bonjour", "merci", "avec")):
        return "fr"
    if words.intersection(("hallo", "danke", "und")):
        return "de"
    if words.intersection(("hello", "the", "how", "you")):
        return "en"
    return None
