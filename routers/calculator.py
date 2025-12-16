from fastapi import APIRouter, FastAPI

router = APIRouter(
    prefix="/calculator",
    tags=["calculator"]
)

app = FastAPI()

@router.get("/sum")
async def sum(x: int = 0, y: int = 10):
    return x + y

app.include_router(router)