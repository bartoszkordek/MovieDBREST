import aiosqlite


class MovieService:
    def __init__(self, connection: aiosqlite.Connection):
        self.connection = connection

    async def get_movies(self) -> list[tuple]:
        query = 'SELECT * FROM movies'
        async with self.connection.execute(query) as cursor:
            movies_list = await cursor.fetchall()
            return movies_list

    async def get_movie(self, movie_id: int) -> tuple | None:
        query = 'SELECT * FROM movies WHERE ID=?'
        async with self.connection.execute(query, (movie_id,)) as cursor:
            movie = await cursor.fetchone()
            return movie

    async def add_movie(self, title: str, year: str, actors: str) -> int:
        query = 'INSERT INTO movies (title, year, actors) VALUES (?, ?, ?)'
        args = (title, year, actors)
        async with self.connection.execute(query, args) as cursor:
            movie_id = cursor.lastrowid
            await self.connection.commit()
            return movie_id

    async def update_movie(self, movie_id: int, title: str, year: str, actors: str) -> bool:
        query = 'UPDATE movies SET title=?, year=?, actors=? WHERE ID=?'
        args = (title, year, actors, movie_id)
        async with self.connection.execute(query, args) as cursor:
            await self.connection.commit()
            return cursor.rowcount > 0

    async def delete_movie(self, movie_id: int) -> bool:
        query = 'DELETE FROM movies WHERE ID=?'
        async with self.connection.execute(query, (movie_id,)) as cursor:
            await self.connection.commit()
            return cursor.rowcount > 0
