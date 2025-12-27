import aiosqlite
from fastapi import APIRouter, HTTPException, Depends, Path

from starlette import status

from database.movies_db_connect import get_db, db_write_lock
from schemas import ActorResponse, ActorMovieResponse, ActorCreateRequest, ActorUpdateRequest
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
    return [{"id": a[0], "name": a[1], "surname": a[2]} for a in actors]


@router.get('/{actor_id}', response_model=ActorResponse)
async def get_single_actor(actor_id: int = Path(..., ge=1, description="Actor ID should be grater or equal 1"),
                           service: ActorService = Depends(get_actor_service)):
    actor = await service.get_actor(actor_id)
    if actor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Actor with ID {actor_id} not found")
    output = {'id': actor[0], 'name': actor[1], 'surname': actor[2]}
    return output


@router.get('/{actor_id}/movies', response_model=list[ActorMovieResponse])
async def get_single_actor_movies(actor_id: int = Path(..., ge=1, description="Actor ID should be grater or equal 1"),
                                  service: ActorService = Depends(get_actor_service)):
    try:
        actor = await service.get_actor(actor_id)
        if actor is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Actor with ID {actor_id} not found")
        movies = await service.get_actor_movies(actor_id)
        if not movies:
            return []
        return [
            {
                "id": m[0],
                "title": m[1],
                "director": m[2],
                "year": m[3],
                "description": m[4]
            } for m in movies
        ]
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post('', status_code=status.HTTP_201_CREATED)
async def add_actor(actor_data: ActorCreateRequest, service: ActorService = Depends(get_actor_service)):
    actor_id = await service.add_actor(
        name=actor_data.name,
        surname=actor_data.surname
    )
    if actor_id is None:
        raise HTTPException(status_code=500, detail="Cannot save actor in database.")

    return {"message": f"Actor {actor_id} added successfully"}


@router.put('/{actor_id}')
async def update_actor(actor_data: ActorUpdateRequest,
                       actor_id: int = Path(..., ge=1, description="Actor ID should be greater or equal 1"),
                       service: ActorService = Depends(get_actor_service)):
    updated_actor = await service.update_actor(
        actor_id=actor_id,
        name=actor_data.name,
        surname=actor_data.surname
    )

    if not updated_actor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actor with ID {actor_id} not found"
        )
    return {"message": f"Actor {actor_id} updated successfully"}


@router.delete('/{actor_id}')
async def delete_actor(actor_id: int = Path(..., ge=1, description="Actor ID should be greater or equal 1"),
                       service: ActorService = Depends(get_actor_service)):
    deleted_actor = await service.delete_actor(actor_id)
    if not deleted_actor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Actor with ID {actor_id} not found"
        )
    return {"message": f"Actor {actor_id} deleted successfully"}
