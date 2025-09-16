from typing import Tuple, Optional, Dict, List

import requests
from fastapi import APIRouter, HTTPException, Depends

from app.api.v1.endpoints.users import get_current_user
from app.db.models.database import db
from app.utils.roles import role_required

router = APIRouter()

# Google Maps API key - You can also fetch this from environment variables or settings
GOOGLE_MAPS_API_KEY = "AIzaSyCl7gQBLcKtKZpph03jOIDGajfp41wdw2k"


def get_address_components(address_components: list) -> Dict[str, str]:
    component_map = {
        "street_number": "",
        "route": "",
        "premise": "",
        "subpremise": "",
        "neighborhood": "",
        "sublocality_level_1": "",
        "sublocality_level_2": "",
        "sublocality_level_3": "",
        "sublocality": "",
        "locality": "",
        "administrative_area_level_1": "",
        "country": "",
        "postal_code": "",
    }

    for component in address_components:
        for type_ in component["types"]:
            if type_ in component_map:
                component_map[type_] = component["long_name"]

    return component_map


def get_address_and_city_from_lat_lon(
    latitude: float, longitude: float, api_key: str
) -> Tuple[Optional[str], Optional[str], Optional[Dict[str, str]], Optional[Dict]]:
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"latlng": f"{latitude},{longitude}", "key": api_key}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK":
            full_address = data["results"][0]["formatted_address"]
            address_components = get_address_components(
                data["results"][0]["address_components"]
            )

            return (
                full_address,
                address_components["locality"],
                address_components,
                data["results"][0],
            )
        else:
            return None, None, None, None
    except requests.exceptions.RequestException:
        return None, None, None, None


def extract_address_parts(full_result: Dict) -> List[str]:
    address_parts = []
    if "address_components" in full_result:
        for component in full_result["address_components"]:
            if "types" in component and "long_name" in component:
                if (
                    "premise" in component["types"]
                    or "subpremise" in component["types"]
                    or "neighborhood" in component["types"]
                ):
                    address_parts.append(component["long_name"])
    return address_parts


@router.post("/check_service", dependencies=[Depends(role_required("provider"))])
def check_service_availability(
    latitude: float, longitude: float, current_user: dict = Depends(get_current_user)
):
    # Get full address, city name, and address components from latitude and longitude
    full_address, city_name, address_components, full_result = (
        get_address_and_city_from_lat_lon(latitude, longitude, GOOGLE_MAPS_API_KEY)
    )

    if not city_name:
        raise HTTPException(
            status_code=400,
            detail="Could not determine the city from the provided coordinates.",
        )

    # Find city in the database
    city = db.cities.find_one({"name": city_name})

    if city:
        # Check if the service is enabled in the city
        # service_enabled = True # just for bypass
        service_enabled = city.get("is_served", False)  # use it for original
        city_id = str(city["_id"])
    else:
        # If city is not found, set service_enabled to False and return the rest of the details
        service_enabled = False  # it was FALSE, for bypass made it true
        city_id = (
            None  # Optionally, you can set city_id to None or some other default value
        )

    # Extract all relevant address parts
    address_parts = extract_address_parts(full_result)

    # Construct street field with all extracted parts
    street = ", ".join(address_parts)

    return {
        "current_address": full_address,
        "street": street,
        "sub_locality": address_components.get("sublocality_level_1")
        or address_components.get("sublocality"),
        "locality": address_components.get("locality"),
        "state": address_components.get("administrative_area_level_1"),
        "pin_code": address_components.get("postal_code"),
        "country": address_components.get("country"),
        "city_name": city_name,
        "city_id": city_id,
        "service_enabled": service_enabled,
    }
