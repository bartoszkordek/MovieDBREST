from fastapi import FastAPI
from routers.actors_router import router as actors_router
from routers.movies_router import router as movies_router

from routers import calculator, geocode, hello

app = FastAPI(title="Movies API 2025")

app.include_router(calculator.router)
app.include_router(geocode.router)
app.include_router(hello.router)
app.include_router(movies_router)
app.include_router(actors_router)


@app.get("/")
async def read_root():
    return {"message": "Hello World"}
