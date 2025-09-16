import logging
from datetime import datetime
from typing import Optional, List, Dict, Tuple

import requests
from bson import ObjectId
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from pydantic import field_validator

from app.api.v1.endpoints.users import get_current_user
from app.api.v1.schemas.address import AddressResponse
from app.db.models.database import motor_db
from app.utils.address_labels import AddressLabel, LabelValidator
from app.utils.roles import role_required

logger = logging.getLogger(__name__)

router = APIRouter()

# Google Maps API key - You can also fetch this from environment variables or settings
GOOGLE_MAPS_API_KEY = "AIzaSyCl7gQBLcKtKZpph03jOIDGajfp41wdw2k"


class AddressCreate(BaseModel):
    apartment_number: str = Field(..., example="123")
    landmark: Optional[str] = Field(None, example="Near Park")
    label: str = Field(..., example="home")
    latitude: float = Field(..., example=28.587287673028868)
    longitude: float = Field(..., example=77.44188595901245)

    @field_validator("label")
    @classmethod
    def validate_label(cls, v: str) -> str:
        normalized_label = AddressLabel.normalize_label(v)  # Use the utility method
        if normalized_label not in AddressLabel.list():
            raise ValueError(f"Label must be one of: {', '.join(AddressLabel.list())}")
        return normalized_label


def get_address_components(address_components: list) -> Dict[str, str]:
    component_map = {
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


@router.post("/address/create", dependencies=[Depends(role_required("provider"))])
async def create_address(
        address: AddressCreate, current_user: dict = Depends(get_current_user)
):
    user_id = current_user["user_id"]

    # Log basic request info
    logger.info(
        f"Create address request: lat={address.latitude}, lon={address.longitude}"
    )

    try:
        # Validate label
        await LabelValidator.validate_label_for_create(user_id, address.label)
    except Exception as e:
        logger.error(f"Label validation failed: {str(e)}")
        raise HTTPException(
            status_code=400, detail=f"Label validation failed: {str(e)}"
        )

    # Get address from coordinates
    try:
        full_address, city_name, address_components, full_result = (
            get_address_and_city_from_lat_lon(
                address.latitude, address.longitude, GOOGLE_MAPS_API_KEY
            )
        )
        logger.info(f"Google Maps result: city_name={city_name}")
    except Exception as e:
        logger.error(f"Google Maps API error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Google Maps API error: {str(e)}")

    if not city_name:
        logger.error("City name not found in Google Maps response")
        raise HTTPException(
            status_code=400,
            detail="Could not determine the city from the provided coordinates.",
        )

    # Find city in database
    city = await motor_db.cities.find_one({"name": city_name})
    if not city:
        logger.error(f"City '{city_name}' not found in database")
        raise HTTPException(
            status_code=404, detail=f"City '{city_name}' not found in database"
        )

    # Check if service is enabled
    service_enabled = city.get("is_served", False)
    if not service_enabled:
        logger.error(f"Service not available in city '{city_name}'")
        raise HTTPException(
            status_code=400, detail=f"Service is not available in city '{city_name}'."
        )

    # Format address
    try:
        full_address = (
            f"{full_address}"
        )

        # Prepare address data
        address_data = {
            "user_id": ObjectId(user_id),
            "address_line1": full_address,
            "apartment_number": address.apartment_number,
            "landmark": address.landmark or None,
            "address_line2": f"{address.apartment_number}, {address.landmark or ''}".strip(
                ", "
            ),
            "location": {
                "type": "Point",
                "coordinates": [address.longitude, address.latitude],
            },
            "label": address.label,
            "address_type": None,
            "sub_locality": address_components.get("sublocality"),
            "locality": address_components.get("locality", ""),
            "state": address_components.get("administrative_area_level_1", ""),
            "pin_code": address_components.get("postal_code", ""),
            "country": address_components.get("country", ""),
            "city_id": city["_id"],
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
            "deleted_at": None,
        }

        # Insert to database
        result = await motor_db.addresses.insert_one(address_data)
        logger.info(f"Address created with ID: {result.inserted_id}")

        return {
            "message": "Address created successfully",
            "address_id": str(result.inserted_id),
            "city_name": city_name,
            "city_id": str(city["_id"]),
            "service_enabled": service_enabled,
        }
    except Exception as e:
        logger.error(f"Error in address creation: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Error in address creation: {str(e)}"
        )


@router.get(
    "/address/list",
    response_model=List[AddressResponse],
    dependencies=[Depends(role_required("provider"))],
)
async def list_addresses(current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["user_id"])

    # Fetch addresses from the database
    addresses = await motor_db.addresses.find(
        {"user_id": user_id, "deleted_at": None}
    ).to_list(length=None)

    # Convert ObjectId fields to strings and format the data
    for address in addresses:
        address["_id"] = str(address["_id"])
        address["user_id"] = str(address["user_id"])
        address["city_id"] = str(address["city_id"])
        if "location" in address:
            address["location"]["coordinates"] = [
                float(coord)
                for coord in address["location"].get("coordinates", [0.0, 0.0])
            ]

    # Return the list of addresses as a response
    return [AddressResponse(**address) for address in addresses]


@router.delete(
    "/address/{id}/delete", dependencies=[Depends(role_required("provider"))]
)
async def delete_address(id: str, current_user: dict = Depends(get_current_user)):
    user_id = ObjectId(current_user["user_id"])
    address = await motor_db.addresses.find_one(
        {"_id": ObjectId(id), "user_id": user_id}
    )

    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    await motor_db.addresses.update_one(
        {"_id": ObjectId(id)}, {"$set": {"deleted_at": datetime.utcnow()}}
    )

    return {"message": "Address deleted successfully", "address_id": id}


@router.put("/address/{id}/update", dependencies=[Depends(role_required("provider"))])
async def update_address(
        id: str, address: AddressCreate, current_user: dict = Depends(get_current_user)
):
    user_id = ObjectId(current_user["user_id"])
    existing_address = await motor_db.addresses.find_one(
        {"_id": ObjectId(id), "user_id": user_id}
    )

    if not existing_address:
        raise HTTPException(status_code=404, detail="Address not found")

    # Get full address, city name, and address components from latitude and longitude
    full_address, city_name, address_components, full_result = (
        get_address_and_city_from_lat_lon(
            address.latitude, address.longitude, GOOGLE_MAPS_API_KEY
        )
    )

    if not city_name:
        raise HTTPException(
            status_code=400,
            detail="Could not determine the city from the provided coordinates.",
        )

    # Find city in the database
    city = await motor_db.cities.find_one({"name": city_name})
    if not city:
        raise HTTPException(status_code=404, detail="City not found in the database.")

    # Check if the service is enabled in the city
    service_enabled = city.get("is_served", False)
    if not service_enabled:
        raise HTTPException(
            status_code=400, detail="Service is not available in this city."
        )

    # Extract relevant address parts for storage
    street = ", ".join(extract_address_parts(full_result))
    full_address = (
        f"{address_components['sublocality']}, {address_components['locality']}, "
        f"{address_components['administrative_area_level_1']}, {address_components['country']}, "
        f"{address_components['postal_code']}".strip(", ")
    )

    # Prepare updated address data
    updated_address_data = {
        "address_line1": full_address,
        "apartment_number": address.apartment_number,
        "landmark": address.landmark or None,
        "address_line2": f"{address.apartment_number}, {address.landmark or ''}".strip(
            ", "
        ),
        "location": {
            "type": "Point",
            "coordinates": [address.longitude, address.latitude],
        },
        "label": address.label,
        "address_type": None,
        "sub_locality": address_components.get("sublocality"),
        "locality": address_components["locality"],
        "state": address_components["administrative_area_level_1"],
        "pin_code": address_components["postal_code"],
        "country": address_components["country"],
        "city_id": city["_id"],
        "updated_at": datetime.utcnow(),
    }

    await motor_db.addresses.update_one(
        {"_id": ObjectId(id)}, {"$set": updated_address_data}
    )

    return {
        "message": "Address updated successfully",
        "address_id": id,
        "city_name": city_name,
        "city_id": str(city["_id"]),
        "service_enabled": service_enabled,
    }
