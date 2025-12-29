import asyncio

import aiosqlite

_MOVIES_DB_NAME = 'movies.db'

db_write_lock = asyncio.Lock()


async def get_db():
    db = await aiosqlite.connect(_MOVIES_DB_NAME, timeout=30.0)
    db.row_factory = aiosqlite.Row
    try:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute("PRAGMA journal_mode = WAL")
        yield db
    finally:
        await db.close()
