import asyncio

import aiosqlite


class MovieService:
    def __init__(self, connection: aiosqlite.Connection, lock: asyncio.Lock):
        self.connection = connection
        self.lock = lock

    async def get_movies(self) -> list[tuple]:
        query = ('SELECT '
                 'm.id, m.title, m.director, m.year, m.description, '
                 'a.id, a.name, a.surname '
                 'FROM movie m '
                 'LEFT JOIN movie_actor_through mat ON m.id = mat.movie_id '
                 'LEFT JOIN actor a ON a.id = mat.actor_id')
        try:
            async with self.connection.execute(query) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    return []

                movies_data = {}
                actors_list = []
                for row in rows:
                    m_id = row[0]

                    if m_id not in movies_data:
                        movies_data[m_id] = {
                            'info': row[0:5],
                            'actors': []
                        }

                    if row[5] is not None:
                        actor_tuple = (row[5], row[6], row[7])
                        movies_data[m_id]['actors'].append(actor_tuple)

                result = []
                for m_id in movies_data:
                    m_info = movies_data[m_id]['info']
                    actors = movies_data[m_id]['actors']
                    result.append((*m_info, actors))

                return result

        except Exception as e:
            print(f"Experienced error during movies select: {e}")
            return []

    async def get_movie(self, movie_id: int) -> tuple | None:
        query = ('SELECT '
                 'm.id, m.title, m.director, m.year, m.description, '
                 'a.id, a.name, a.surname '
                 'FROM movie m '
                 'LEFT JOIN movie_actor_through mat ON m.id = mat.movie_id '
                 'LEFT JOIN actor a ON a.id = mat.actor_id '
                 'WHERE m.id = ?')
        try:
            async with self.connection.execute(query, (movie_id,)) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    return None

                first_row = rows[0]
                m_id, m_title, m_director, m_year, m_desc = first_row[0:5]

                actors_list = []
                for row in rows:
                    if row[5] is not None:
                        actor_tuple = (row[5], row[6], row[7])
                        actors_list.append(actor_tuple)

                return m_id, m_title, m_director, m_year, m_desc, actors_list

        except Exception as e:
            print(f"Experienced error during movie {movie_id} select: {e}")
            return None

    async def add_movie(self, title: str, director: str, year: int, description: str, actors_ids: list[int]) -> int:
        add_movie_query = 'INSERT INTO movie (title, director, year, description) VALUES (?, ?, ?, ?)'
        add_movie_args = (title, director, year, description)
        add_movie_and_actor_relation_query = 'INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (?, ?)'

        async with self.lock:
            try:
                await self.connection.execute("BEGIN")

                async with self.connection.execute(add_movie_query, add_movie_args) as cursor:
                    movie_id = cursor.lastrowid

                    if actors_ids:
                        add_movie_and_actor_relation_args = [(movie_id, actor_id) for actor_id in actors_ids]
                        await self.connection.executemany(add_movie_and_actor_relation_query,
                                                          add_movie_and_actor_relation_args)
                    await self.connection.commit()

                    return movie_id

            except Exception as e:
                await self.connection.rollback()
                print(f"Experienced error during add movie: {e}")
                raise e

    async def update_movie(self, movie_id: int, title: str, director: str, year: int, description: str,
                           actors_ids: list[int]) -> bool:
        update_movie_query = 'UPDATE movie SET title=?, director=?, year=?, description=? WHERE id=?'
        update_movie_args = (title, director, year, description, movie_id)
        delete_movie_and_actor_relation_query = 'DELETE FROM movie_actor_through WHERE movie_id=?'
        add_movie_and_actor_relation_query = 'INSERT INTO movie_actor_through (movie_id, actor_id) VALUES (?, ?)'

        async with self.lock:
            try:
                await self.connection.execute("BEGIN")

                async with self.connection.execute(update_movie_query, update_movie_args) as cursor:
                    if cursor.rowcount == 0:
                        await self.connection.rollback()
                        return False

                    await self.connection.execute(delete_movie_and_actor_relation_query, (movie_id,))

                    if actors_ids:
                        add_movie_and_actor_relation_args = [(movie_id, actor_id) for actor_id in actors_ids]
                        await self.connection.executemany(add_movie_and_actor_relation_query,
                                                          add_movie_and_actor_relation_args)

                    await self.connection.commit()
                    return True

            except Exception as e:
                await self.connection.rollback()
                print(f"Experienced error during movie {movie_id} update: {e}")
                return False

    async def delete_movie(self, movie_id: int) -> bool:
        select_movie_query = 'SELECT 1 FROM movie WHERE id=?'
        delete_movie_and_actor_relation_query = 'DELETE FROM movie_actor_through WHERE movie_id=?'
        delete_movie_query = 'DELETE FROM movie WHERE id=?'

        async with self.lock:
            try:
                await self.connection.execute("BEGIN")

                async with self.connection.execute(select_movie_query, (movie_id,)) as cursor:
                    if not await cursor.fetchone():
                        await self.connection.rollback()
                        return False

                await self.connection.execute(delete_movie_and_actor_relation_query, (movie_id,))

                cursor = await self.connection.execute(delete_movie_query, (movie_id,))
                if cursor.rowcount == 0:
                    await self.connection.rollback()
                    return False

                await self.connection.commit()
                return True

            except Exception as e:
                await self.connection.rollback()
                print(f"Experienced error during movie {movie_id} delete: {e}")
                return False
