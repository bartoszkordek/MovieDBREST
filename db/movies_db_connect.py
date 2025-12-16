import sqlite3

_MOVIES_DB_NAME = 'movies.db'


def get_movies():
    connection = sqlite3.connect(_MOVIES_DB_NAME)
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT * FROM movies')
        movies_list = cursor.fetchall()
        return movies_list
    finally:
        connection.close()


def get_movie(movie_id: int):
    connection = sqlite3.connect(_MOVIES_DB_NAME)
    cursor = connection.cursor()
    query = 'SELECT * FROM movies WHERE ID=?'
    try:
        cursor.execute(query, (movie_id,))
        movie = cursor.fetchone()
        return movie
    finally:
        connection.close()


def save_movie(title: str, year: str, actors: str):
    connection = sqlite3.connect(_MOVIES_DB_NAME)
    cursor = connection.cursor()
    save_query = 'INSERT INTO movies (title, year, actors) VALUES (?, ?, ?)'
    save_args = (title, year, actors)
    get_query = 'SELECT * FROM movies WHERE ID=?'
    try:
        cursor.execute(save_query, save_args)
        connection.commit()

        movie_id = cursor.lastrowid
        cursor.execute(get_query, (movie_id,))
        movie = cursor.fetchone()
        return movie
    finally:
        connection.close()


def update_movie(movie_id: int, title: str, year: str, actors: str):
    connection = sqlite3.connect(_MOVIES_DB_NAME)
    cursor = connection.cursor()
    update_query = 'UPDATE movies SET title=?, year=?, actors=? WHERE ID=?'
    update_args = (title, year, actors, movie_id)
    get_query = 'SELECT * FROM movies WHERE ID=?'
    try:
        cursor.execute(update_query, update_args)
        connection.commit()

        if cursor.rowcount == 0:
            return None
        cursor.execute(get_query, (movie_id,))
        movie = cursor.fetchone()
        return movie
    finally:
        connection.close()


def delete_movie(movie_id: int):
    connection = sqlite3.connect(_MOVIES_DB_NAME)
    cursor = connection.cursor()
    query = 'DELETE FROM movies WHERE ID=?'
    try:
        cursor.execute(query, (movie_id,))
        connection.commit()
        return cursor.rowcount > 0
    finally:
        connection.close()
