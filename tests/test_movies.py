import pytest
from fastapi import status
from main import app
from database.movies_db_connect import get_db


async def test_get_movies_format(client, test_db_conn):
    await test_db_conn.execute("INSERT INTO actor (id, name, surname) VALUES (1, 'Tom', 'Hanks')")
    await test_db_conn.execute(
        "INSERT INTO movie (id, title, director, year) VALUES (10, 'Sully', 'Clint Eastwood', 2016)")
    await test_db_conn.execute("INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (10, 1)")
    await test_db_conn.commit()

    response = await client.get("/movies")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()[0]

    assert data["title"] == "Sully"
    assert len(data["actors"]) == 1
    assert data["actors"][0]["name"] == "Tom"
    assert "id" in data["actors"][0]


async def test_get_all_movies_empty_database(client):
    """Checks if GET /movies returns an empty list when no records exist."""
    response = await client.get("/movies")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_get_single_movie_success(client, test_db_conn):
    await test_db_conn.execute("INSERT INTO actor (id, name, surname) VALUES (1, 'Tom', 'Hanks')")
    await test_db_conn.execute(
        "INSERT INTO movie (id, title, director, year) VALUES (10, 'Sully', 'Clint Eastwood', 2016)")
    await test_db_conn.execute("INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (10, 1)")
    await test_db_conn.commit()

    response = await client.get(f"/movies/10")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["id"] == 10
    assert data["title"] == "Sully"
    assert data["director"] == "Clint Eastwood"
    assert data["year"] == 2016

    assert len(data["actors"]) == 1
    assert data["actors"][0]["id"] == 1
    assert data["actors"][0]["name"] == "Tom"
    assert data["actors"][0]["surname"] == "Hanks"


async def test_add_movie_success(client, test_db_conn):
    await test_db_conn.execute("INSERT INTO actor (name, surname) VALUES ('Tom', 'Hardy')")
    await test_db_conn.commit()

    movie_payload = {
        "title": "Inception",
        "director": "Christopher Nolan",
        "year": 2010,
        "description": "Dream within a dream",
        "actors": [1]
    }

    response = await client.post("/movies", json=movie_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Movie 1 added successfully"}

    async with test_db_conn.execute(
            "SELECT title, director, year, description FROM movie WHERE id = 1"
    ) as cursor:
        movie_row = await cursor.fetchone()
        assert movie_row is not None
        assert movie_row['title'] == "Inception"
        assert movie_row['director'] == "Christopher Nolan"
        assert movie_row['year'] == 2010
        assert movie_row['description'] == "Dream within a dream"

    async with test_db_conn.execute(
            "SELECT actor_id FROM movie_actor_through WHERE movie_id = 1"
    ) as cursor:
        relation_row = await cursor.fetchone()
        assert relation_row is not None
        assert relation_row[0] == 1


async def test_add_movie_without_actors_success(client, test_db_conn):
    payload = {
        "title": "Solo Movie",
        "director": "Independent",
        "year": 2025,
        "actors": []
    }
    response = await client.post("/movies", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    async with test_db_conn.execute("SELECT id FROM movie WHERE title = 'Solo Movie'") as cursor:
        assert await cursor.fetchone() is not None


async def test_update_movie_success(client, test_db_conn):
    actors = [('Tom', 'Hanks'), ('Tom', 'Hardy'), ('Leonardo', 'DiCaprio')]
    await test_db_conn.executemany("INSERT INTO actor (name, surname) VALUES (?, ?)", actors)
    await test_db_conn.execute(
        "INSERT INTO movie (id, title, director, year, description) VALUES (1, 'Old Title', 'Old Director', 2000, 'Old Description')"
    )
    await test_db_conn.executemany(
        "INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (?, ?)",
        [(1, 1), (1, 2)]
    )
    await test_db_conn.commit()

    updated_movie_payload = {
        "title": "Inception",
        "director": "Christopher Nolan",
        "year": 2010,
        "description": "Dream within a dream",
        "actors": [2, 3]
    }

    response = await client.put(f"/movies/1", json=updated_movie_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Movie 1 updated successfully"}

    async with test_db_conn.execute(
            "SELECT title, director, year, description FROM movie WHERE id = 1"
    ) as cursor:
        movie_row = await cursor.fetchone()
        assert movie_row is not None
        assert movie_row['title'] == "Inception"
        assert movie_row['director'] == "Christopher Nolan"
        assert movie_row['year'] == 2010
        assert movie_row['description'] == "Dream within a dream"

    async with test_db_conn.execute(
            "SELECT actor_id FROM movie_actor_through WHERE movie_id = 1"
    ) as cursor:
        relation_rows = await cursor.fetchall()
        assert len(relation_rows) == 2
        updated_actor_ids = [row[0] for row in relation_rows]
        assert set(updated_actor_ids) == {2, 3}
        assert 1 not in set(updated_actor_ids)


@pytest.mark.parametrize("method, url", [("POST", "/movies"), ("PUT", "/movies/1")])
@pytest.mark.parametrize("payload, expected_error", [
    # --- Numeric Validation (Year) ---
    ({"title": "A", "director": "B", "year": 1800, "actors": []}, "greater_than_equal"),
    ({"title": "A", "director": "B", "year": 2200, "actors": []}, "less_than_equal"),
    ({"title": "A", "director": "B", "year": "not-a-year", "actors": []}, "int_parsing"),

    # --- String Validation (Title & Director) ---
    ({"title": "", "director": "B", "year": 2024, "actors": []}, "string_too_short"),
    ({"title": "A", "director": "", "year": 2024, "actors": []}, "string_too_short"),
    ({"title": "  ", "director": "B", "year": 2024, "actors": []}, "string_too_short"),
    ({"title": "a" * 201, "director": "B", "year": 2024, "actors": []}, "string_too_long"),
    ({"title": "A", "director": "b" * 101, "year": 2024, "actors": []}, "string_too_long"),

    # --- Description Validation ---
    ({"title": "A", "director": "B", "year": 2024, "description": "x" * 2001, "actors": []}, "string_too_long"),

    # --- Actors List Validation ---
    ({"title": "A", "director": "B", "year": 2024, "actors": list(range(101))}, "too_long"),
    ({"title": "A", "director": "B", "year": 2024, "actors": ["not-an-id"]}, "int_parsing"),
    ({"title": "A", "director": "B", "year": 2024, "actors": "not-a-list"}, "list_type"),

    # --- Missing Required Fields ---
    ({"director": "B", "year": 2024, "actors": []}, "missing"),
    ({"title": "A", "year": 2024, "actors": []}, "missing"),
    ({"title": "A", "director": "B", "actors": []}, "missing"),

    # --- Special Characters (Security/XSS) ---
    ({"title": "<script>alert(1)</script>", "director": "B", "year": 2024, "actors": []}, "value_error"),
])
async def test_movie_validation_errors(client, test_db_conn, method, url, payload, expected_error):
    if method == "PUT":
        await test_db_conn.execute("INSERT INTO movie (id, title, director, year) VALUES (1, 'T', 'D', 2000)")
        await test_db_conn.commit()

    response = None
    match method:
        case "POST":
            response = await client.post(url, json=payload)
        case "PUT":
            response = await client.put(url, json=payload)

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert expected_error in str(response.json()).lower()


async def test_delete_movie_success(client, test_db_conn):
    actors = [('Tom', 'Hanks'), ('Tom', 'Hardy'), ('Leonardo', 'DiCaprio')]
    await test_db_conn.executemany("INSERT INTO actor (name, surname) VALUES (?, ?)", actors)
    await test_db_conn.execute(
        "INSERT INTO movie (id, title, director, year, description) VALUES (1, 'Inception', 'Christopher Nolan', 2010, 'Dream within a dream')"
    )
    await test_db_conn.executemany(
        "INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (?, ?)",
        [(1, 2), (1, 3)]
    )
    await test_db_conn.commit()

    response = await client.delete(f"/movies/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Movie 1 deleted successfully"}

    async with test_db_conn.execute("SELECT 1 FROM movie WHERE id = 1") as cursor:
        assert await cursor.fetchone() is None

    async with test_db_conn.execute("SELECT 1 FROM movie_actor_through WHERE movie_id = 1") as cursor:
        assert await cursor.fetchone() is None

    async with test_db_conn.execute("SELECT COUNT(*) FROM actor WHERE id IN (1, 2, 3)") as cursor:
        count = (await cursor.fetchone())[0]
        assert count == 3


@pytest.mark.parametrize("method", ["GET", "PUT", "DELETE"])
async def test_not_existing_movie_id(client, method):
    not_existing_movie_id = 999
    url = f"/movies/{not_existing_movie_id}"

    response = None
    match method:
        case "GET":
            response = await client.get(url)
        case "PUT":
            response = await client.put(url, json={"title": "A", "director": "B", "year": 2024, "actors": []})
        case "DELETE":
            response = await client.delete(url)

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Movie with ID {not_existing_movie_id} not found"


@pytest.mark.asyncio
async def test_get_movies_database_crash(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_db_connection.execute.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.get("/movies")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Internal Server Error"}
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_single_movie_database_crash(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_db_connection.execute.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.get("/movies/1")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_add_movie_database_crash_on_commit(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_cursor = mocker.AsyncMock()
    mock_db_connection.execute.return_value.__aenter__.return_value = mock_cursor

    mock_db_connection.commit.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        movie_payload = {
            "title": "Inception",
            "director": "Nolan",
            "year": 2010,
            "description": "Dream within a dream",
            "actors": [1, 2]
        }
        response = await client.post("/movies", json=movie_payload)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert mock_db_connection.rollback.called
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_update_movie_database_crash_on_commit(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_cursor = mocker.AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_connection.execute.return_value.__aenter__.return_value = mock_cursor

    mock_db_connection.commit.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        update_payload = {
            "title": "New Title",
            "director": "New Director",
            "year": 2024,
            "description": "Updated",
            "actors": []
        }
        response = await client.put("/movies/1", json=update_payload)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert mock_db_connection.rollback.called
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_delete_movie_database_crash_on_commit(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_cursor = mocker.AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_connection.execute.return_value.__aenter__.return_value = mock_cursor

    mock_db_connection.commit.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.delete("/movies/1")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert mock_db_connection.rollback.called
    finally:
        app.dependency_overrides = {}
