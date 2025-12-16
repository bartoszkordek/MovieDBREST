from fastapi import FastAPI

from routers import calculator, geocode, hello, movies

app = FastAPI()

app.include_router(calculator.router)
app.include_router(geocode.router)
app.include_router(hello.router)
app.include_router(movies.router)

@app.get("/")
async def read_root():
    return {"message": "Hello World"}