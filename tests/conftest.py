import pytest
import aiosqlite
from httpx import AsyncClient, ASGITransport
from main import app
from database.movies_db_connect import get_db

SCHEMA = """
CREATE TABLE actor (
   id INTEGER PRIMARY KEY,
   name VARCHAR(256),
   surname VARCHAR(256)
);
CREATE TABLE movie (
   id INTEGER PRIMARY KEY,
   title VARCHAR(256),
   director VARCHAR(256),
   year INTEGER,
   description TEXT
);

CREATE TABLE movie_actor_through (
   id INTEGER PRIMARY KEY,
   movie_id INTEGER NOT NULL,
   actor_id INTEGER NOT NULL,
   FOREIGN KEY(movie_id) REFERENCES movie(id) ON DELETE CASCADE,
   FOREIGN KEY(actor_id) REFERENCES actor(id) ON DELETE CASCADE
);
"""


@pytest.fixture
async def test_db_conn():
    async with aiosqlite.connect(":memory:") as db:
        db.row_factory = aiosqlite.Row
        await db.execute("PRAGMA foreign_keys = ON")
        await db.executescript(SCHEMA)
        yield db


@pytest.fixture(autouse=True)
async def override_get_db(test_db_conn):
    async def _get_test_db():
        yield test_db_conn

    app.dependency_overrides[get_db] = _get_test_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    transport = ASGITransport(app=app, raise_app_exceptions=False)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
