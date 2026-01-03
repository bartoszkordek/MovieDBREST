from fastapi import APIRouter

router = APIRouter(
    prefix="/hello",
    tags=["hello"]
)


@router.get("/{name}")
async def say_hello(name: str):
    return name
