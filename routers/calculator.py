from fastapi import APIRouter

router = APIRouter(
    prefix="/calculator",
    tags=["calculator"]
)


@router.get("/sum")
async def sum(x: int = 0, y: int = 10):
    return x + y
