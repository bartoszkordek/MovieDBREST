from typing import Any

from fastapi import FastAPI, HTTPException
import requests
from starlette import status

import db_connect

app = FastAPI()


@app.get("/")
async def read_root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return name


@app.get("/sum")
async def sum(x: int = 0, y: int = 10):
    return x + y


@app.get("/geocode")
def geocode(lat: float, lon: float):
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    return response.json()


@app.get('/movies')
def get_movies():
    movies = db_connect.get_movies()
    output = []
    for m in movies:
        movie = {'id': f'{m[0]}', 'title': f'{m[1]}', 'year': f'{m[2]}', 'actors': f'{m[3]}'}
        output.append(movie)
    return output


@app.get('/movies/{movie_id}')
def get_single_movie(movie_id: int):
    movie = db_connect.get_movie(movie_id)
    if movie is None:
        return {'message': f'Movie not found'}
    movie_json = {'id': f'{movie[0]}', 'title': f'{movie[1]}', 'year': f'{movie[2]}', 'actors': f'{movie[3]}'}
    return movie_json


@app.post('/movies')
def add_movie(params: dict[str, Any]):
    title = params['title']
    year = params['year']
    actors = params['actors']
    movie = db_connect.save_movie(title, year, actors)
    return {"message": f"Movie {movie[0]} added successfully"}


@app.put('/movies/{movie_id}')
def update_movie(movie_id: int, params: dict[str, Any]):
    title = params['title']
    year = params['year']
    actors = params['actors']
    movie = db_connect.update_movie(movie_id, title, year, actors)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found"
        )
    return {"message": f"Movie {movie[0]} updated successfully"}


@app.delete('/movies/{movie_id}')
def delete_movie(movie_id: int):
    deleted_movie = db_connect.delete_movie(movie_id)
    if not deleted_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found"
        )
    return {"message": f"Movie {movie_id} deleted successfully"}
