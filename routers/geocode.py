from fastapi import APIRouter, FastAPI, HTTPException
import requests

router = APIRouter(
    prefix="/geocode",
    tags=["geocode"]
)


@router.get("")
def geocode(lat: float, lon: float):
    url = f"https://nominatim.openstreetmap.org/reverse?format=jsonv2&lat={lat}&lon={lon}"

    response = requests.get(url, headers={"User-Agent": "MovieDB_Educational_App/1.0"})
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(status_code=response.status_code, detail="Cannot pull geolocalization data.")
