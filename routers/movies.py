from fastapi import APIRouter, FastAPI, HTTPException
from typing import Any

from starlette import status

from db import movies_db_connect

router = APIRouter(
    prefix="/movies",
    tags=["movies"]
)

app = FastAPI()

@router.get('/')
def get_movies():
    movies = movies_db_connect.get_movies()
    output = []
    for m in movies:
        movie = {'id': f'{m[0]}', 'title': f'{m[1]}', 'year': f'{m[2]}', 'actors': f'{m[3]}'}
        output.append(movie)
    return output


@router.get('/{movie_id}')
def get_single_movie(movie_id: int):
    movie = movies_db_connect.get_movie(movie_id)
    if movie is None:
        return {'message': f'Movie not found'}
    movie_json = {'id': f'{movie[0]}', 'title': f'{movie[1]}', 'year': f'{movie[2]}', 'actors': f'{movie[3]}'}
    return movie_json


@router.post('/')
def add_movie(params: dict[str, Any]):
    title = params['title']
    year = params['year']
    actors = params['actors']
    movie = movies_db_connect.save_movie(title, year, actors)
    return {"message": f"Movie {movie[0]} added successfully"}


@router.put('/{movie_id}')
def update_movie(movie_id: int, params: dict[str, Any]):
    title = params['title']
    year = params['year']
    actors = params['actors']
    movie = movies_db_connect.update_movie(movie_id, title, year, actors)
    if movie is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found"
        )
    return {"message": f"Movie {movie[0]} updated successfully"}


@router.delete('/{movie_id}')
def delete_movie(movie_id: int):
    deleted_movie = movies_db_connect.delete_movie(movie_id)
    if not deleted_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found"
        )
    return {"message": f"Movie {movie_id} deleted successfully"}

app.include_router(router)