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
    assert response.status_code == 201
    assert response.json() == {"message": "Movie 1 added successfully"}

    async with test_db_conn.execute(
            "SELECT title, director, year, description FROM movie WHERE id = 1"
    ) as cursor:
        movie_row = await cursor.fetchone()
        assert movie_row is not None
        assert movie_row[0] == "Inception"
        assert movie_row[1] == "Christopher Nolan"
        assert movie_row[2] == 2010
        assert movie_row[3] == "Dream within a dream"

    async with test_db_conn.execute(
            "SELECT actor_id FROM movie_actor_through WHERE movie_id = 1"
    ) as cursor:
        relation_row = await cursor.fetchone()
        assert relation_row is not None
        assert relation_row[0] == 1


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
    assert response.status_code == 200
    assert response.json() == {"message": "Movie 1 updated successfully"}

    async with test_db_conn.execute(
            "SELECT title, director, year, description FROM movie WHERE id = 1"
    ) as cursor:
        movie_row = await cursor.fetchone()
        assert movie_row is not None
        assert movie_row[0] == "Inception"
        assert movie_row[1] == "Christopher Nolan"
        assert movie_row[2] == 2010
        assert movie_row[3] == "Dream within a dream"

    async with test_db_conn.execute(
            "SELECT actor_id FROM movie_actor_through WHERE movie_id = 1"
    ) as cursor:
        relation_rows = await cursor.fetchall()
        assert len(relation_rows) == 2
        updated_actor_ids = [row[0] for row in relation_rows]
        assert set(updated_actor_ids) == {2, 3}
        assert 1 not in set(updated_actor_ids)


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
    assert response.status_code == 200
    assert response.json() == {"message": "Movie 1 deleted successfully"}

    async with test_db_conn.execute("SELECT 1 FROM movie WHERE id = 1") as cursor:
        assert await cursor.fetchone() is None

    async with test_db_conn.execute("SELECT 1 FROM movie_actor_through WHERE movie_id = 1") as cursor:
        assert await cursor.fetchone() is None

    async with test_db_conn.execute("SELECT COUNT(*) FROM actor WHERE id IN (1, 2, 3)") as cursor:
        count = (await cursor.fetchone())[0]
        assert count == 3
