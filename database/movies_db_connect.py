import aiosqlite

_MOVIES_DB_NAME = 'movies_1.db'

async def get_db():
    db = await aiosqlite.connect(_MOVIES_DB_NAME)
    try:
        yield db
    finally:
        await db.close()