import asyncio
import aiosqlite

from loguru import logger

from exceptions import ActorNotFoundError

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
            logger.exception("Database error while fetching actors list")
            raise

    async def get_actor(self, actor_id: int) -> dict | None:
        query = 'SELECT id, name, surname FROM actor WHERE id=?'
        try:
            async with self.connection.execute(query, (actor_id,)) as cursor:
                actor = await cursor.fetchone()
                if actor is None:
                    return None
                return dict(actor)
        except Exception:
            logger.exception("Database error while fetching actor {}", actor_id)
            raise

    async def get_actor_movies(self, actor_id: int) -> list[dict]:
        check_actor_query = 'SELECT 1 FROM actor WHERE id=?'
        actor_movies_relation_query = (
            'SELECT m.id, m.title, m.director, m.year, m.description '
            'FROM movie m '
            'INNER JOIN movie_actor_through mat ON mat.movie_id=m.id '
            'WHERE mat.actor_id=?'
        )
        try:
            async with self.connection.execute(
                    check_actor_query,
                    (actor_id,)
            ) as cursor:
                if not await cursor.fetchone():
                    logger.warning("Actor with ID {} not found", actor_id)
                    raise ActorNotFoundError(actor_id)

            async with self.connection.execute(
                    actor_movies_relation_query,
                    (actor_id,)
            ) as cursor:
                movies = await cursor.fetchall()
                return [dict(movie) for movie in movies]
        except ActorNotFoundError:
            raise
        except Exception:
            logger.exception(
                "Database error while fetching movies for actor {}",
                actor_id
            )
            raise

    async def add_actor(self, name: str, surname: str) -> int:
        query = 'INSERT INTO actor (name, surname) VALUES (?, ?)'
        args = (name, surname)
        async with self.lock:
            try:
                await self.connection.execute("BEGIN IMMEDIATE")

                async with self.connection.execute(query, args) as cursor:
                    actor_id = cursor.lastrowid

                    if actor_id is None:
                        logger.error(
                            "Error occurred while adding actor: {} {}. "
                            "Failed to retrieve actor ID.",
                            name,
                            surname
                        )
                        raise Exception(f"Failed to retrieve actor {name} {surname} ID")

                    await self.connection.commit()
                    logger.info(
                        "Successfully added new actor: {} {} (ID: {})",
                        name,
                        surname,
                        actor_id
                    )
                    return actor_id
            except Exception:
                await self.connection.rollback()
                logger.exception(
                    "Database error while adding actor: {} {}",
                    name,
                    surname
                )
                raise

    async def update_actor(self, actor_id: int, name: str, surname: str) -> None:
        query = 'UPDATE actor SET name=?, surname=? WHERE id=?'
        args = (name, surname, actor_id)
        async with self.lock:
            try:
                await self.connection.execute("BEGIN IMMEDIATE")

                async with self.connection.execute(query, args) as cursor:
                    if cursor.rowcount == 0:
                        await self.connection.rollback()
                        logger.info(f"Actor with id {actor_id} not found for update")
                        raise ActorNotFoundError(actor_id)

                await self.connection.commit()
                logger.info(f"Successfully updated actor {actor_id}: {name} {surname}")

            except ActorNotFoundError:
                raise
            except Exception:
                await self.connection.rollback()
                logger.exception(
                    "Database error during update of actor {}: {} {}",
                    actor_id,
                    name,
                    surname
                )
                raise

    async def delete_actor(self, actor_id: int) -> None:
        select_actor_query = 'SELECT 1 FROM actor WHERE id=?'
        delete_actor_relation_query = ('DELETE FROM movie_actor_through '
                                       'WHERE actor_id=?')
        delete_actor_query = 'DELETE FROM actor WHERE id=?'
        async with self.lock:
            try:
                await self.connection.execute("BEGIN IMMEDIATE")

                async with self.connection.execute(
                        select_actor_query,
                        (actor_id,)
                ) as cursor:
                    if not await cursor.fetchone():
                        await self.connection.rollback()
                        logger.info(f"Actor {actor_id} not found")
                        raise ActorNotFoundError(actor_id)

                await self.connection.execute(delete_actor_relation_query, (actor_id,))
                await self.connection.execute(delete_actor_query, (actor_id,))

                await self.connection.commit()
                logger.info(f"Successfully deleted actor {actor_id}")

            except ActorNotFoundError:
                raise
            except Exception:
                await self.connection.rollback()
                logger.exception(f"Database error during deletion of actor {actor_id}")
                raise
