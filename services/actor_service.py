import asyncio

import aiosqlite


class ActorService:
    def __init__(self, connection: aiosqlite.Connection, lock: asyncio.Lock):
        self.connection = connection
        self.lock = lock

    async def get_actors(self) -> list[tuple]:
        query = 'SELECT * FROM actor'
        try:
            async with self.connection.execute(query) as cursor:
                actors_list = await cursor.fetchall()
                return actors_list
        except Exception as e:
            print(f"Experienced error during actors select: {e}")
            return []

    async def get_actor(self, actor_id: int) -> tuple | None:
        query = 'SELECT * FROM actor WHERE id=?'
        try:
            async with self.connection.execute(query, (actor_id,)) as cursor:
                actor = await cursor.fetchone()
                return actor
        except Exception as e:
            print(f"Experienced error during actor {actor_id} select: {e}")
            return None

    async def get_actor_movies(self, actor_id: int) -> list[tuple]:
        check_actor_query = 'SELECT 1 FROM actor WHERE id=?'
        actor_movies_relation_query = ('SELECT movie.* FROM movie '
                                       'INNER JOIN movie_actor_through ON movie_actor_through.movie_id=movie.id '
                                       'WHERE actor_id=?')
        try:
            async with self.connection.execute(check_actor_query, (actor_id,)) as cursor:
                if not await cursor.fetchone():
                    raise ValueError(f"Actor with ID {actor_id} not found")

            async with self.connection.execute(actor_movies_relation_query, (actor_id,)) as cursor:
                movies = await cursor.fetchall()
                return movies
        except Exception as e:
            print(f"Experienced error during actor movies {actor_id} select: {e}")
            return []

    async def add_actor(self, name: str, surname: str) -> int:
        query = 'INSERT INTO actor (name, surname) VALUES (?, ?)'
        args = (name, surname)
        async with self.lock:
            try:
                async with self.connection.execute(query, args) as cursor:
                    actor_id = cursor.lastrowid

                    if actor_id is None:
                        raise Exception("Failed to retrieve actor ID")

                    await self.connection.commit()
                    return actor_id
            except Exception as e:
                await self.connection.rollback()
                print(f"Experienced error during add actor: {e}")
                raise e

    async def update_actor(self, actor_id: int, name: str, surname: str) -> bool:
        query = 'UPDATE actor SET name=?, surname=? WHERE id=?'
        args = (name, surname, actor_id)
        async with self.lock:
            try:
                async with self.connection.execute(query, args) as cursor:
                    if cursor.rowcount == 0:
                        await self.connection.rollback()
                        return False
                await self.connection.commit()
                return True
            except Exception as e:
                await self.connection.rollback()
                print(f"Experienced error during actor {actor_id} update: {e}")
                return False

    async def delete_actor(self, actor_id: int) -> bool:
        select_actor_query = 'SELECT 1 FROM actor WHERE id=?'
        delete_actor_relation_query = 'DELETE FROM movie_actor_through WHERE actor_id=?'
        delete_actor_query = 'DELETE FROM actor WHERE id=?'
        async with self.lock:
            try:
                await self.connection.execute("BEGIN")

                async with self.connection.execute(select_actor_query, (actor_id,)) as cursor:
                    if not await cursor.fetchone():
                        await self.connection.rollback()
                        return False

                await self.connection.execute(delete_actor_relation_query, (actor_id,))

                cursor = await self.connection.execute(delete_actor_query, (actor_id,))
                if cursor.rowcount == 0:
                    await self.connection.rollback()
                    return False

                await self.connection.commit()
                return True

            except Exception as e:
                await self.connection.rollback()
                print(f"Experienced error during actor {actor_id} delete: {e}")
                return False
