from fastapi import APIRouter, FastAPI
import requests

router = APIRouter(
    prefix="/geocode",
    tags=["geocode"]
)

app = FastAPI()

@router.get("/")
def geocode(lat: float, lon: float):
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    return response.json()

app.include_router(router)