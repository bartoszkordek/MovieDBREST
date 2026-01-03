import pytest
from fastapi import status
from main import app
from database.movies_db_connect import get_db


@pytest.mark.asyncio
async def test_search_actors(client, test_db_conn):
    actors = [
        ("Tom", "Hanks"),
        ("Tom", "Hardy"),
        ("Cillian", "Murphy")
    ]
    await test_db_conn.executemany(
        "INSERT INTO actor (name, surname) VALUES (?, ?)",
        actors
    )
    await test_db_conn.commit()

    response = await client.get("/actors")

    assert response.status_code == 200
    results = response.json()

    assert len(results) == 3
    surnames = [r["surname"] for r in results]
    assert "Hanks" in surnames
    assert "Hardy" in surnames
    assert "Murphy" in surnames


async def test_get_all_actors_empty_database(client):
    """Checks if GET /actors returns an empty list when no records exist."""
    response = await client.get("/actors")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == []


async def test_get_single_actor_success(client, test_db_conn):
    await test_db_conn.execute(
        "INSERT INTO actor (name, surname) VALUES (?, ?)",
        ("Cillian", "Murphy")
    )
    await test_db_conn.commit()

    response = await client.get("/actors/1")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Cillian"
    assert data["surname"] == "Murphy"
    assert data["id"] == 1


async def test_add_actor_success(client, test_db_conn):
    actor_payload = {
        "name": "Tom",
        "surname": "Hanks"
    }

    response = await client.post("/actors", json=actor_payload)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json() == {"message": "Actor 1 added successfully"}

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 1"
    ) as cursor:
        movie_row = await cursor.fetchone()
        assert movie_row is not None
        assert movie_row['name'] == "Tom"
        assert movie_row['surname'] == "Hanks"


async def test_add_actor_whitespace_cleaning(client, test_db_conn):
    payload = {
        "name": "  Tom  ",
        "surname": "  Hanks  "
    }
    response = await client.post("/actors", json=payload)
    assert response.status_code == status.HTTP_201_CREATED

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 1"
    ) as cursor:
        row = await cursor.fetchone()
        assert row[0] == "Tom"
        assert row[1] == "Hanks"


@pytest.mark.parametrize("name, surname", [
    ("Kowalska-Wyśniewska", "Nowak"),
    ("John", "O'Connor"),
    ("J.R.R.", "Tolkien"),
    ("Stanisław", "Żółć"),
    ("Łukasz", "Wiśniewski"),
])
async def test_add_actor_complex_names_success(client, test_db_conn, name, surname):
    payload = {"name": name, "surname": surname}
    response = await client.post("/actors", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor ORDER BY id DESC LIMIT 1"
    ) as cursor:
        row = await cursor.fetchone()
        assert row['name'] == name
        assert row['surname'] == surname


@pytest.mark.parametrize("payload, error_loc", [
    ({"name": "<script>", "surname": "Hanks"}, "name"),
    ({"name": "Tom", "surname": "<b>Hanks</b>"}, "surname"),
    ({"name": "Tom;", "surname": "DROP TABLE--"}, "name"),
    ({"name": "Tom", "surname": "{json: body}"}, "surname"),
])
async def test_add_actor_special_chars_validation(client, payload, error_loc):
    response = await client.post("/actors", json=payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert any(error_loc in err["loc"] for err in response.json()["detail"])


async def test_update_actor_success(client, test_db_conn):
    actors = [('Old Name', 'Old Surname'), ('Tom', 'Hardy')]
    await test_db_conn.executemany(
        "INSERT INTO actor (name, surname) VALUES (?, ?)",
        actors
    )
    await test_db_conn.commit()

    actor_id = 1
    updated_actor_payload = {
        "name": "Tom",
        "surname": "Hanks"
    }

    response = await client.put(f"/actors/{actor_id}", json=updated_actor_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Actor 1 updated successfully"}

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 1"
    ) as cursor:
        actor_row = await cursor.fetchone()
        assert actor_row is not None
        assert tuple(actor_row) == ("Tom", "Hanks")

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 2"
    ) as cursor:
        actor_row = await cursor.fetchone()
        assert actor_row is not None
        assert tuple(actor_row) == ("Tom", "Hardy")


@pytest.mark.parametrize("method, url", [
    ("POST", "/actors"),
    ("PUT", "/actors/1")
])
@pytest.mark.parametrize("payload, error_loc, expected_error", [
    # --- Custom Validator: Digits ---
    ({"name": "Tom1", "surname": "Hanks"}, "name", "cannot contain digits"),
    ({"name": "Tom", "surname": "Hanks2"}, "surname", "cannot contain digits"),

    # --- Custom Validator: Special Characters (XSS/Injection) ---
    ({"name": "<script>", "surname": "Hanks"}, "name", "Field contains special characters"),
    ({"name": "Tom", "surname": "Hanks#"}, "surname", "Field contains special characters"),
    ({"name": "Tom;", "surname": "Hanks"}, "name", "Field contains special characters"),
    ({"name": "Tom", "surname": "{json: body}"}, "surname", "Field contains special characters"),
    ({"name": "Tom", "surname": "<b>Hanks</b>"}, "surname", "Field contains special characters"),

    # --- Pydantic: String Length (min_length / max_length) ---
    ({"name": "", "surname": "Hanks"}, "name", "string_too_short"),
    ({"name": "Tom", "surname": ""}, "surname", "string_too_short"),
    ({"name": "a" * 51, "surname": "Hanks"}, "name", "string_too_long"),
    ({"name": "Tom", "surname": "s" * 101}, "surname", "string_too_long"),

    # --- Pydantic: Whitespace stripping ---
    ({"name": "   ", "surname": "Hanks"}, "name", "string_too_short"),
    ({"name": "Tom", "surname": "   "}, "surname", "string_too_short"),

    # --- Pydantic: Missing Fields ---
    ({"name": "Tom"}, "surname", "Field required"),
    ({"surname": "Hanks"}, "name", "Field required"),
    ({}, ["name", "surname"], "Field required"),

    # --- Pydantic: Invalid Data Types ---
    ({"name": 123, "surname": "Hanks"}, "name", "string_type"),
    ({"name": "Tom", "surname": 123}, "surname", "string_type"),
    ({"name": 123, "surname": 123}, ["name", "surname"], "string_type"),
    ({"name": [], "surname": []}, ["name", "surname"], "string_type"),
])
async def test_actor_validation_unified(client, test_db_conn, method, url, payload, error_loc, expected_error):
    if method == "PUT":
        await test_db_conn.execute("INSERT INTO actor (id, name, surname) VALUES (1, 'Old', 'Name')")
        await test_db_conn.commit()

    response = None
    match method:
        case "POST":
            response = await client.post(url, json=payload)
        case "PUT":
            response = await client.put(url, json=payload)
        case _:
            raise ValueError(f"Method {method} not supported")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    response_json = response.json()
    error_details = str(response_json["detail"]).lower()

    assert expected_error.lower() in error_details

    if isinstance(error_loc, list):
        for field in error_loc:
            assert any(field in str(err["loc"]) for err in response_json["detail"])
    else:
        assert any(error_loc in str(err["loc"]) for err in response_json["detail"])


async def test_delete_actor_success(client, test_db_conn):
    actors = [('Tom', 'Hanks'), ('Tom', 'Hardy')]
    await test_db_conn.executemany(
        "INSERT INTO actor (name, surname) VALUES (?, ?)",
        actors
    )
    await test_db_conn.commit()

    response = await client.delete("/actors/1")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Actor 1 deleted successfully"}

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 1"
    ) as cursor:
        assert await cursor.fetchone() is None

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 2"
    ) as cursor:
        actor_row = await cursor.fetchone()
        assert actor_row is not None
        assert tuple(actor_row) == ("Tom", "Hardy")


async def test_delete_actor_and_relations_success(client, test_db_conn):
    actors = [('Tom', 'Hanks'), ('Tom', 'Hardy')]
    await test_db_conn.executemany(
        "INSERT INTO actor (name, surname) VALUES (?, ?)",
        actors
    )
    await test_db_conn.execute(
        "INSERT INTO movie (id, title, director, year) "
        "VALUES (10, 'Inception', 'Nolan', 2010)"
    )
    await test_db_conn.execute(
        "INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (10, 1)"
    )
    await test_db_conn.commit()

    response = await client.delete("/actors/1")
    assert response.status_code == status.HTTP_200_OK

    async with test_db_conn.execute(
            "SELECT * FROM movie_actor_through WHERE actor_id = 1"
    ) as cursor:
        relation = await cursor.fetchone()
        assert relation is None

    async with test_db_conn.execute(
            "SELECT title FROM movie WHERE id = 10"
    ) as cursor:
        movie = await cursor.fetchone()
        assert movie is not None
        assert movie[0] == "Inception"

    async with test_db_conn.execute(
            "SELECT name FROM actor WHERE id = 2"
    ) as cursor:
        other_actor = await cursor.fetchone()
        assert other_actor is not None


async def test_delete_actor_without_movies_success(client, test_db_conn):
    """Checks if deleting an actor without any movie relations works correctly."""
    await test_db_conn.execute(
        "INSERT INTO actor (id, name, surname) VALUES (?, ?, ?)",
        (5, 'Tom', 'Hanks')
    )
    await test_db_conn.commit()

    response = await client.delete("/actors/5")

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"message": "Actor 5 deleted successfully"}

    async with test_db_conn.execute("SELECT * FROM actor WHERE id = 5") as cursor:
        assert await cursor.fetchone() is None


async def test_get_actor_movies_success(client, test_db_conn):
    await test_db_conn.execute(
        "INSERT INTO actor (id, name, surname) VALUES (?, ?, ?)",
        (1, 'Tom', 'Hanks')
    )
    await test_db_conn.executemany(
        "INSERT INTO movie (id, title, director, year, description) VALUES (?, ?, ?, ?, ?)",
        [(10, 'Cast Away', 'Zemeckis', 2000, 'Island'), (11, 'Sully', 'Eastwood', 2016, 'Plane')]
    )
    await test_db_conn.executemany(
        "INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (?, ?)",
        [(10, 1), (11, 1)]
    )
    await test_db_conn.commit()

    response = await client.get("/actors/1/movies")

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Cast Away"
    assert data[1]["title"] == "Sully"


@pytest.mark.parametrize("method", ["GET", "GET_MOVIES", "PUT", "DELETE"])
async def test_not_existing_actor_id(client, method):
    actor_id = 999
    payload = {"name": "Tom", "surname": "Hanks"}
    response = None

    match method:
        case "GET":
            response = await client.get(f"/actors/{actor_id}")
        case "GET_MOVIES":
            response = await client.get(f"/actors/{actor_id}/movies")
        case "PUT":
            response = await client.put(f"/actors/{actor_id}", json=payload)
        case "DELETE":
            response = await client.delete(f"/actors/{actor_id}")
        case _:
            raise ValueError(f"Unknown method: {method}")

    assert response is not None
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json()["detail"] == f"Actor with ID {actor_id} not found"


@pytest.mark.parametrize("method", ["GET", "GET_MOVIES", "PUT", "DELETE"])
@pytest.mark.parametrize("invalid_id", ["abc", 0, -5])
async def test_actor_id_validation_error(client, method, invalid_id):
    """Validation if API returns 422 response in case of invalid value or format of ID (e.g. 'abc' or value < 1)"""

    payload = {"name": "Tom", "surname": "Hanks"}
    response = None

    match method:
        case "GET":
            response = await client.get(f"/actors/{invalid_id}")
        case "GET_MOVIES":
            response = await client.get(f"/actors/{invalid_id}/movies")
        case "PUT":
            response = await client.put(f"/actors/{invalid_id}", json=payload)
        case "DELETE":
            response = await client.delete(f"/actors/{invalid_id}")
        case _:
            raise ValueError(f"Unsupported method: {method}")

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    errors = response.json()["detail"]
    assert any("actor_id" in err["loc"] for err in errors)
    assert any("path" in err["loc"] for err in errors)


@pytest.mark.asyncio
async def test_get_actors_database_crash(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_db_connection.execute.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.get("/actors")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Internal Server Error"}
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_single_actor_database_crash(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_db_connection.execute.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.get("/actors/1")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_get_actor_movies_database_crash(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_db_connection.execute.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.get("/actors/1/movies")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_add_actor_database_crash_on_commit(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_cursor = mocker.AsyncMock()
    mock_db_connection.execute.return_value.__aenter__.return_value = mock_cursor

    mock_db_connection.commit.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.post("/actors", json={"name": "John", "surname": "Doe"})

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert mock_db_connection.rollback.called
    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_update_actor_database_crash_api_response(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_cursor = mocker.AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_connection.execute.return_value.__aenter__.return_value = mock_cursor

    mock_db_connection.commit.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection

    try:
        response = await client.put("/actors/1", json={"name": "A", "surname": "B"})
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json() == {"detail": "Internal Server Error"}
        assert mock_db_connection.rollback.called

    finally:
        app.dependency_overrides = {}


@pytest.mark.asyncio
async def test_delete_actor_database_crash_on_commit(client, mocker):
    mock_db_connection = mocker.AsyncMock()
    mock_cursor = mocker.AsyncMock()
    mock_cursor.rowcount = 1
    mock_db_connection.execute.return_value.__aenter__.return_value = mock_cursor

    mock_db_connection.commit.side_effect = Exception("Critical Database Failure")

    app.dependency_overrides[get_db] = lambda: mock_db_connection
    try:
        response = await client.delete("/actors/1")

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert mock_db_connection.rollback.called
    finally:
        app.dependency_overrides = {}
