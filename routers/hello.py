from fastapi import APIRouter, FastAPI

router = APIRouter(
    prefix="/hello",
    tags=["hello"]
)

app = FastAPI()

@router.get("/{name}")
async def say_hello(name: str):
    return name

app.include_router(router)