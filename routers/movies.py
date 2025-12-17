import aiosqlite
from fastapi import APIRouter, FastAPI, HTTPException, Depends
from typing import Any

from starlette import status

from database.movies_db_connect import get_db
from services.movie_service import MovieService

router = APIRouter(
    prefix="/movies",
    tags=["movies"]
)

app = FastAPI()


def get_movie_service(db: aiosqlite.Connection = Depends(get_db)):
    return MovieService(db)


@router.get('')
async def get_movies(service: MovieService = Depends(get_movie_service)):
    movies = await service.get_movies()
    output = []
    for m in movies:
        movie = {'id': f'{m[0]}', 'title': f'{m[1]}', 'year': f'{m[2]}', 'actors': f'{m[3]}'}
        output.append(movie)
    return output


@router.get('/{movie_id}')
async def get_single_movie(movie_id: int, service: MovieService = Depends(get_movie_service)):
    movie = await service.get_movie(movie_id)
    if movie is None:
        return {'message': f'Movie not found'}
    movie_json = {'id': f'{movie[0]}', 'title': f'{movie[1]}', 'year': f'{movie[2]}', 'actors': f'{movie[3]}'}
    return movie_json


@router.post('')
async def add_movie(params: dict[str, Any], service: MovieService = Depends(get_movie_service)):
    title = params['title']
    year = params['year']
    actors = params['actors']
    movie_id = await service.add_movie(title, year, actors)
    if movie_id is None:
        raise HTTPException(status_code=500, detail="Cannot save move in database.")

    return {"message": f"Movie {movie_id} added successfully"}


@router.put('/{movie_id}')
async def update_movie(movie_id: int, params: dict[str, Any], service: MovieService = Depends(get_movie_service)):
    title = params['title']
    year = params['year']
    actors = params['actors']
    updated_movie = await service.update_movie(movie_id, title, year, actors)

    if not updated_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found"
        )
    return {"message": f"Movie {movie_id} updated successfully"}


@router.delete('/{movie_id}')
async def delete_movie(movie_id: int, service: MovieService = Depends(get_movie_service)):
    deleted_movie = await service.delete_movie(movie_id)
    if not deleted_movie:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Movie with ID {movie_id} not found"
        )
    return {"message": f"Movie {movie_id} deleted successfully"}


app.include_router(router)
