import aiosqlite
from fastapi import APIRouter, HTTPException, Depends, Path, status

from database.movies_db_connect import get_db, db_write_lock
from exceptions import MovieNotFoundError
from schemas import MovieCreateRequest, MovieUpdateRequest, MovieResponse
from services.movie_service import MovieService

router = APIRouter(
    prefix="/movies",
    tags=["movies"]
)


def get_movie_service(db: aiosqlite.Connection = Depends(get_db)):
    return MovieService(db, db_write_lock)


@router.get('', response_model=list[MovieResponse])
async def get_movies(service: MovieService = Depends(get_movie_service)):
    movies = await service.get_movies()
    return movies


@router.get('/{movie_id}', response_model=MovieResponse)
async def get_single_movie(movie_id: int = Path(..., ge=1, description="Movie ID should be greater or equal 1"),
                           service: MovieService = Depends(get_movie_service)):
    movie = await service.get_movie(movie_id)
    if movie is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Movie with ID {movie_id} not found")
    return movie


@router.post('', status_code=status.HTTP_201_CREATED)
async def add_movie(movie_data: MovieCreateRequest, service: MovieService = Depends(get_movie_service)):
    movie_id = await service.add_movie(
        title=movie_data.title,
        director=movie_data.director,
        year=movie_data.year,
        description=movie_data.description,
        actors_ids=movie_data.actors
    )

    return {"message": f"Movie {movie_id} added successfully"}


@router.put('/{movie_id}')
async def update_movie(movie_data: MovieUpdateRequest,
                       movie_id: int = Path(..., ge=1, description="Movie ID should be greater or equal 1"),
                       service: MovieService = Depends(get_movie_service)):
    try:
        await service.update_movie(
            movie_id=movie_id,
            title=movie_data.title,
            director=movie_data.director,
            year=movie_data.year,
            description=movie_data.description,
            actors_ids=movie_data.actors
        )

        return {"message": f"Movie {movie_id} updated successfully"}
    except MovieNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete('/{movie_id}')
async def delete_movie(movie_id: int = Path(..., ge=1, description="Movie ID should be greater or equal 1"),
                       service: MovieService = Depends(get_movie_service)):
    try:
        await service.delete_movie(movie_id)
        return {"message": f"Movie {movie_id} deleted successfully"}
    except MovieNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
