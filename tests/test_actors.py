async def test_add_actor_success(client, test_db_conn):
    actor_payload = {
        "name": "Tom",
        "surname": "Hanks"
    }

    response = await client.post("/actors", json=actor_payload)
    assert response.status_code == 201
    assert response.json() == {"message": "Actor 1 added successfully"}

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 1"
    ) as cursor:
        movie_row = await cursor.fetchone()
        assert movie_row is not None
        assert movie_row[0] == "Tom"
        assert movie_row[1] == "Hanks"


async def test_update_actor_success(client, test_db_conn):
    actors = [('Old Name', 'Old Surname'), ('Tom', 'Hardy')]
    await test_db_conn.executemany("INSERT INTO actor (name, surname) VALUES (?, ?)", actors)
    await test_db_conn.commit()

    actor_id = 1
    updated_actor_payload = {
        "name": "Tom",
        "surname": "Hanks"
    }

    response = await client.put(f"/actors/{actor_id}", json=updated_actor_payload)
    assert response.status_code == 200
    assert response.json() == {"message": "Actor 1 updated successfully"}

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 1"
    ) as cursor:
        actor_row = await cursor.fetchone()
        assert actor_row is not None
        assert actor_row == ("Tom", "Hanks")

    async with test_db_conn.execute(
            "SELECT name, surname FROM actor WHERE id = 2"
    ) as cursor:
        actor_row = await cursor.fetchone()
        assert actor_row is not None
        assert actor_row == ("Tom", "Hardy")


async def test_delete_actor_success(client, test_db_conn):
    actors = [('Tom', 'Hanks'), ('Tom', 'Hardy')]
    await test_db_conn.executemany("INSERT INTO actor (name, surname) VALUES (?, ?)", actors)
    await test_db_conn.commit()

    response = await client.delete("/actors/1")
    assert response.status_code == 200
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
        assert actor_row == ("Tom", "Hardy")


async def test_delete_actor_and_relations_success(client, test_db_conn):
    actors = [('Tom', 'Hanks'), ('Tom', 'Hardy')]
    await test_db_conn.executemany("INSERT INTO actor (name, surname) VALUES (?, ?)", actors)
    await test_db_conn.execute(
        "INSERT INTO movie (id, title, director, year) VALUES (10, 'Inception', 'Nolan', 2010)"
    )
    await test_db_conn.execute(
        "INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (10, 1)"
    )
    await test_db_conn.commit()

    response = await client.delete("/actors/1")
    assert response.status_code == 200

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


async def test_get_actor_movies_success(client, test_db_conn):
    await test_db_conn.execute("INSERT INTO actor (id, name, surname) VALUES (1, 'Tom', 'Hanks')")
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

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Cast Away"
    assert data[1]["title"] == "Sully"
