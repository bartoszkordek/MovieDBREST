import asyncio
import aiosqlite

from loguru import logger

from exceptions import MovieNotFoundError

logger.add("logs/movie_service.log", rotation="10 MB", level="INFO")


class MovieService:
    def __init__(self, connection: aiosqlite.Connection, lock: asyncio.Lock):
        self.connection = connection
        self.lock = lock

    async def get_movies(self) -> list[dict]:
        query = (
            'SELECT '
            'm.id AS movie_id, m.title, m.director, m.year, m.description, '
            'a.id AS actor_id, a.name, a.surname '
            'FROM movie m '
            'LEFT JOIN movie_actor_through mat ON m.id = mat.movie_id '
            'LEFT JOIN actor a ON a.id = mat.actor_id'
        )
        try:
            async with self.connection.execute(query) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    return []

                movies_data = {}
                for row in rows:
                    movie_id = row['movie_id']

                    if movie_id not in movies_data:
                        movies_data[movie_id] = {
                            'id': row['movie_id'],
                            'title': row['title'],
                            'director': row['director'],
                            'year': row['year'],
                            'description': row['description'],
                            'actors': []
                        }

                    if row['actor_id'] is not None:
                        movies_data[movie_id]['actors'].append({
                            'id': row['actor_id'],
                            'name': row['name'],
                            'surname': row['surname']
                        })

                return list(movies_data.values())

        except Exception:
            logger.exception("Database error while fetching actors list")
            raise

    async def get_movie(self, movie_id: int) -> dict | None:
        query = (
            'SELECT '
            'm.id AS movie_id, m.title, m.director, m.year, m.description, '
            'a.id AS actor_id, a.name, a.surname '
            'FROM movie m '
            'LEFT JOIN movie_actor_through mat ON m.id = mat.movie_id '
            'LEFT JOIN actor a ON a.id = mat.actor_id '
            'WHERE m.id = ?'
        )
        try:
            async with self.connection.execute(query, (movie_id,)) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    return None

                first_row = rows[0]
                movie = {
                    'id': first_row['movie_id'],
                    'title': first_row['title'],
                    'director': first_row['director'],
                    'year': first_row['year'],
                    'description': first_row['description'],
                    'actors': []
                }

                for row in rows:
                    if row['actor_id'] is not None:
                        movie['actors'].append({
                            'id': row['actor_id'],
                            'name': row['name'],
                            'surname': row['surname']
                        })

                return movie
        except Exception:
            logger.exception(f"Database error while fetching movie {movie_id}")
            raise

    async def add_movie(
            self,
            title: str,
            director: str,
            year: int,
            description: str,
            actors_ids: list[int]
    ) -> int:
        add_movie_query = """
                    INSERT INTO movie (title, director, year, description)
                    VALUES (?, ?, ?, ?)
                """
        add_movie_args = (title, director, year, description)

        add_movie_and_actor_relation_query = """
                    INSERT INTO movie_actor_through (movie_id, actor_id)
                    VALUES (?, ?)
                """

        async with self.lock:
            try:
                await self.connection.execute("BEGIN IMMEDIATE")

                async with self.connection.execute(
                        add_movie_query,
                        add_movie_args
                ) as cursor:
                    movie_id = cursor.lastrowid

                    if actors_ids:
                        add_movie_and_actor_relation_args = [
                            (movie_id, actor_id) for actor_id in actors_ids
                        ]
                        await self.connection.executemany(
                            add_movie_and_actor_relation_query,
                            add_movie_and_actor_relation_args
                        )
                    await self.connection.commit()

                    logger.info(
                        "Successfully added new movie: {} (ID: {})",
                        title,
                        movie_id
                    )
                    return movie_id

            except Exception:
                await self.connection.rollback()
                logger.exception(
                    "Database error while adding movie: {}, {}, {}, {}",
                    title,
                    director,
                    year,
                    description
                )
                raise

    async def update_movie(
            self,
            movie_id: int,
            title: str,
            director: str,
            year: int,
            description: str,
            actors_ids: list[int]
    ) -> None:
        update_movie_query = """
            UPDATE movie
            SET title = ?, director = ?, year = ?, description = ?
            WHERE id = ?
        """
        update_movie_args = (title, director, year, description, movie_id)
        delete_movie_and_actor_relation_query = """
            DELETE FROM movie_actor_through
            WHERE movie_id=?
        """
        add_movie_and_actor_relation_query = """
            INSERT INTO movie_actor_through (movie_id, actor_id)
            VALUES (?, ?)
        """
        async with self.lock:
            try:
                await self.connection.execute("BEGIN IMMEDIATE")

                async with self.connection.execute(
                        update_movie_query,
                        update_movie_args
                ) as cursor:
                    if cursor.rowcount == 0:
                        await self.connection.rollback()
                        raise MovieNotFoundError(movie_id)

                    await self.connection.execute(
                        delete_movie_and_actor_relation_query,
                        (movie_id,)
                    )

                    if actors_ids:
                        add_movie_and_actor_relation_args = [
                            (movie_id, actor_id) for actor_id in actors_ids
                        ]
                        await self.connection.executemany(
                            add_movie_and_actor_relation_query,
                            add_movie_and_actor_relation_args
                        )

                    await self.connection.commit()
                    logger.info("Successfully updated movie {}", movie_id)

            except MovieNotFoundError:
                raise
            except Exception:
                await self.connection.rollback()
                logger.exception(
                    "Database error during update of movie {}: {}",
                    movie_id,
                    title
                )
                raise

    async def delete_movie(self, movie_id: int) -> bool:
        select_movie_query = 'SELECT 1 FROM movie WHERE id=?'
        delete_movie_and_actor_relation_query = """
            DELETE FROM movie_actor_through
            WHERE movie_id=?
        """
        delete_movie_query = 'DELETE FROM movie WHERE id=?'

        async with self.lock:
            try:
                await self.connection.execute("BEGIN IMMEDIATE")

                async with self.connection.execute(
                        select_movie_query,
                        (movie_id,)
                ) as cursor:
                    if not await cursor.fetchone():
                        await self.connection.rollback()
                        raise MovieNotFoundError(movie_id)

                await self.connection.execute(
                    delete_movie_and_actor_relation_query,
                    (movie_id,)
                )
                await self.connection.execute(
                    delete_movie_query,
                    (movie_id,)
                )

                await self.connection.commit()
                logger.info("Successfully deleted movie {}", movie_id)
                return True

            except MovieNotFoundError:
                raise
            except Exception:
                await self.connection.rollback()
                logger.exception(
                    "Database error during deletion of movie {}",
                    movie_id
                )
                raise
