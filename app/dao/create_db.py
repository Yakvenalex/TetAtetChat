import aiosqlite
import json

from app.config import settings


async def create_users_table():
    async with aiosqlite.connect(settings.DB_PATH) as db:
        await db.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            nickname TEXT NOT NULL,
            gender TEXT NOT NULL,
            age INTEGER NOT NULL,
            is_available INTEGER DEFAULT 1,  -- 1 = True, 0 = False
            current_room INTEGER DEFAULT NULL,
            preferences TEXT DEFAULT '{}'
        )
        ''')
        await db.commit()
