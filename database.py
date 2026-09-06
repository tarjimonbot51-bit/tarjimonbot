from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import aiosqlite


class Database:
    def __init__(self, path: str):
        self.path = Path(path)

    async def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        async with aiosqlite.connect(self.path) as db:
            await db.executescript(
                """
                PRAGMA foreign_keys = ON;
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    full_name TEXT NOT NULL,
                    selected_source_language TEXT NOT NULL DEFAULT 'auto',
                    selected_target_language TEXT NOT NULL DEFAULT 'en',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS translations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    source_language TEXT NOT NULL,
                    target_language TEXT NOT NULL,
                    source_text TEXT NOT NULL,
                    translated_text TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
                );
                CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id);
                CREATE INDEX IF NOT EXISTS idx_translations_user_id ON translations(user_id);
                CREATE INDEX IF NOT EXISTS idx_translations_created_at ON translations(created_at);
                """
            )
            await db.commit()

    async def upsert_user(self, user_id: int, username: str | None, full_name: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO users (user_id, username, full_name, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET username = excluded.username,
                full_name = excluded.full_name""",
                (user_id, username, full_name, now),
            )
            await db.commit()

    async def get_user(self, user_id: int) -> dict[str, Any] | None:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def update_languages(self, user_id: int, source: str, target: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "UPDATE users SET selected_source_language = ?, selected_target_language = ? WHERE user_id = ?",
                (source, target, user_id),
            )
            await db.commit()

    async def save_translation(self, user_id: int, source: str, target: str, source_text: str, translated_text: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """INSERT INTO translations
                (user_id, source_language, target_language, source_text, translated_text, created_at)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, source, target, source_text, translated_text, datetime.now(timezone.utc).isoformat()),
            )
            await db.commit()

    async def get_history(self, user_id: int, limit: int, offset: int) -> list[dict[str, Any]]:
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """SELECT * FROM translations WHERE user_id = ?
                ORDER BY id DESC LIMIT ? OFFSET ?""",
                (user_id, limit, offset),
            )
            return [dict(row) for row in await cursor.fetchall()]

    async def count_user_history(self, user_id: int) -> int:
        return await self._count("SELECT COUNT(*) FROM translations WHERE user_id = ?", (user_id,))

    async def count_users(self) -> int:
        return await self._count("SELECT COUNT(*) FROM users")

    async def count_today_users(self) -> int:
        today = datetime.now(timezone.utc).date().isoformat()
        return await self._count("SELECT COUNT(*) FROM users WHERE substr(created_at, 1, 10) = ?", (today,))

    async def count_translations(self) -> int:
        return await self._count("SELECT COUNT(*) FROM translations")

    async def get_all_user_ids(self) -> list[int]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute("SELECT user_id FROM users")
            rows = await cursor.fetchall()
            return [int(row[0]) for row in rows]

    async def _count(self, query: str, params: tuple = ()) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(query, params)
            row = await cursor.fetchone()
            return int(row[0])
