from fastapi import APIRouter, HTTPException
import requests

router = APIRouter(
    prefix="/geocode",
    tags=["geocode"]
)


@router.get("")
def geocode(lat: float, lon: float):
    base_url = "https://nominatim.openstreetmap.org/reverse"
    url = f"{base_url}?format=jsonv2&lat={lat}&lon={lon}"

    response = requests.get(
        url,
        headers={"User-Agent": "MovieDB_Educational_App/1.0"}
    )
    if response.status_code == 200:
        return response.json()
    else:
        raise HTTPException(
            status_code=response.status_code,
            detail="Cannot pull geolocalization data."
        )
