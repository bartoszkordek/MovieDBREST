import asyncio
import aiosqlite

from loguru import logger

logger.add("logs/actor_service.log", rotation="10 MB", level="INFO")


class ActorService:
    def __init__(self, connection: aiosqlite.Connection, lock: asyncio.Lock):
        self.connection = connection
        self.lock = lock

    async def get_actors(self) -> list[dict]:
        query = 'SELECT id, name, surname FROM actor'
        try:
            async with self.connection.execute(query) as cursor:
                actors_list = await cursor.fetchall()
                return [dict(actor) for actor in actors_list]
        except Exception:
            logger.exception("Failed to fetch actors list from database")
            return []

    async def get_actor(self, actor_id: int) -> dict | None:
        query = 'SELECT id, name, surname FROM actor WHERE id=?'
        try:
            async with self.connection.execute(query, (actor_id,)) as cursor:
                actor = await cursor.fetchone()
                return dict(actor)
        except Exception:
            logger.exception(f"Failed to fetch {actor_id} from database")
            return None

    async def get_actor_movies(self, actor_id: int) -> list[dict]:
        check_actor_query = 'SELECT 1 FROM actor WHERE id=?'
        actor_movies_relation_query = ('SELECT m.id, m.title, m.director, m.year, m.description '
                                       'FROM movie m '
                                       'INNER JOIN movie_actor_through mat ON mat.movie_id=m.id '
                                       'WHERE mat.actor_id=?')
        try:
            async with self.connection.execute(check_actor_query, (actor_id,)) as cursor:
                if not await cursor.fetchone():
                    logger.warning(f"Actor with ID {actor_id} not found")
                    raise ValueError(f"Actor with ID {actor_id} not found")

            async with self.connection.execute(actor_movies_relation_query, (actor_id,)) as cursor:
                movies = await cursor.fetchall()
                return [dict(movie) for movie in movies]
        except Exception:
            logger.exception(f"Experienced error during fetching actor {actor_id} movies")
            return []

    async def add_actor(self, name: str, surname: str) -> int:
        query = 'INSERT INTO actor (name, surname) VALUES (?, ?)'
        args = (name, surname)
        async with self.lock:
            try:
                async with self.connection.execute(query, args) as cursor:
                    actor_id = cursor.lastrowid

                    if actor_id is None:
                        logger.exception(
                            f"Error occurred while adding actor: {name} {surname}. Failed to retrieve actor ID.")
                        raise Exception("Failed to retrieve actor ID")

                    await self.connection.commit()
                    logger.info(f"Successfully added new actor: {name} {surname} (ID: {actor_id})")
                    return actor_id
            except Exception as e:
                await self.connection.rollback()
                logger.exception(f"Error occurred while adding actor: {name} {surname}")
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
                logger.info(f"Successfully updated actor {actor_id}")
                return True
            except Exception:
                await self.connection.rollback()
                logger.exception(f"Experienced error during actor {actor_id} update")
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
                logger.info(f"Successfully deleted actor {actor_id}")
                return True

            except Exception:
                await self.connection.rollback()
                logger.exception(f"Experienced error during actor {actor_id} delete")
                return False
