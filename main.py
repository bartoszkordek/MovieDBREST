from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger

from exceptions import ActorNotFoundError
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


@app.exception_handler(ActorNotFoundError)
async def actor_not_found_exception_handler(request: Request, exc: ActorNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": exc.message},
    )


@app.exception_handler(Exception)
async def global_exception_handler(_: Request, exc: Exception):
    logger.exception("An unexpected error occurred in the application")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal Server Error"}
    )
