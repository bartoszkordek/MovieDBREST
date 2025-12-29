from fastapi import APIRouter, FastAPI

router = APIRouter(
    prefix="/hello",
    tags=["hello"]
)


@router.get("/{name}")
async def say_hello(name: str):
    return name
