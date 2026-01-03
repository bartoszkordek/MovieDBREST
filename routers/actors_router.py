import aiosqlite
from fastapi import APIRouter, HTTPException, Depends, Path, status

from database.movies_db_connect import get_db, db_write_lock
from exceptions import ActorNotFoundError
from schemas import (
    ActorResponse,
    ActorMovieResponse,
    ActorCreateRequest,
    ActorUpdateRequest
)
from services.actor_service import ActorService

router = APIRouter(
    prefix="/actors",
    tags=["actors"]
)


def get_actor_service(db: aiosqlite.Connection = Depends(get_db)):
    return ActorService(db, db_write_lock)


@router.get('', response_model=list[ActorResponse])
async def get_actors(service: ActorService = Depends(get_actor_service)):
    actors = await service.get_actors()
    return actors


@router.get('/{actor_id}', response_model=ActorResponse)
async def get_single_actor(actor_id: int = Path(
    ...,
    ge=1,
    description="Actor ID should be greater or equal 1"),
        service: ActorService = Depends(get_actor_service)
):
    actor = await service.get_actor(actor_id)
    if actor is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actor with ID {actor_id} not found",
        )
    return actor


@router.get("/{actor_id}/movies", response_model=list[ActorMovieResponse])
async def get_single_actor_movies(
        actor_id: int = Path(
            ...,
            ge=1,
            description="Actor ID should be greater or equal 1"
        ),
        service: ActorService = Depends(get_actor_service),
):
    try:
        return await service.get_actor_movies(actor_id)
    except ActorNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post('', status_code=status.HTTP_201_CREATED)
async def add_actor(
        actor_data: ActorCreateRequest,
        service: ActorService = Depends(get_actor_service)
):
    actor_id = await service.add_actor(
        name=actor_data.name,
        surname=actor_data.surname
    )
    return {"message": f"Actor {actor_id} added successfully"}


@router.put('/{actor_id}')
async def update_actor(
        actor_data: ActorUpdateRequest,
        actor_id: int = Path(
            ...,
            ge=1,
            description="Actor ID should be greater or equal 1"),
        service: ActorService = Depends(get_actor_service)
):
    try:
        await service.update_actor(
            actor_id=actor_id,
            name=actor_data.name,
            surname=actor_data.surname
        )
        return {"message": f"Actor {actor_id} updated successfully"}
    except ActorNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.delete('/{actor_id}')
async def delete_actor(
        actor_id: int = Path(
            ...,
            ge=1,
            description="Actor ID should be greater or equal 1"),
        service: ActorService = Depends(get_actor_service)
):
    try:
        await service.delete_actor(actor_id)
        return {"message": f"Actor {actor_id} deleted successfully"}
    except ActorNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
