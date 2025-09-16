from bson import ObjectId
from fastapi import APIRouter, HTTPException

from app.api.v1.schemas.rate import Rate
from app.db.models.database import db

router = APIRouter()


@router.post("/rates")
def create_or_update_rate(rate: Rate):
    # Convert city_id and category_id to ObjectId
    rate.city_id = ObjectId(rate.city_id)
    rate.category_id = ObjectId(rate.category_id)

    existing_rate = db.rates.find_one(
        {"city_id": rate.city_id, "category_id": rate.category_id}
    )

    if existing_rate:
        db.rates.update_one(
            {"_id": existing_rate["_id"]},
            {
                "$set": {
                    "rate_per_hour": rate.rate_per_hour,
                    "min_hourly_rate": rate.min_hourly_rate,
                    "max_hourly_rate": rate.max_hourly_rate,
                }
            },
        )
        return {"message": "Rate updated successfully"}
    else:
        db.rates.insert_one(rate.dict())
        return {"message": "Rate submitted successfully"}


@router.get("/rate/fetch")
async def fetch_rate(city_id: str, category_id: str):
    city_id = ObjectId(city_id)
    category_id = ObjectId(category_id)

    rate_data = db.rates.find_one({"city_id": city_id, "category_id": category_id})
    if not rate_data:
        raise HTTPException(
            status_code=404, detail="Rate not found for the given city and category"
        )

    return {
        "city_id": str(city_id),
        "category_id": str(category_id),
        "rate_per_hour": rate_data["rate_per_hour"],
        "min_hourly_rate": rate_data["min_hourly_rate"],
        "max_hourly_rate": rate_data["max_hourly_rate"],
    }


@router.get("/rates/{city_id}")
async def get_rates_for_city(city_id: str):
    city_id = ObjectId(city_id)
    rates = list(db.rates.find({"city_id": city_id}))
    for rate in rates:
        rate["_id"] = str(rate["_id"])
        rate["city_id"] = str(rate["city_id"])
        rate["category_id"] = str(rate["category_id"])
    return {"rates": rates}


@router.get("/rate/fetch-by-address")
async def fetch_rate_by_address(address_id: str, category_id: str):
    address_id = ObjectId(address_id)
    category_id = ObjectId(category_id)

    address = db.addresses.find_one({"_id": address_id})
    if not address:
        raise HTTPException(status_code=404, detail="Address not found")

    city_id = address.get("city_id")
    if not city_id:
        raise HTTPException(
            status_code=404, detail="City ID not found for the given address"
        )

    rate_data = db.rates.find_one({"city_id": city_id, "category_id": category_id})
    if not rate_data:
        raise HTTPException(
            status_code=404, detail="Rate not found for the given address and category"
        )

    return {
        "address_id": str(address_id),
        "city_id": str(city_id),
        "category_id": str(category_id),
        "rate_per_hour": rate_data["rate_per_hour"],
        "min_hourly_rate": rate_data["min_hourly_rate"],
        "max_hourly_rate": rate_data["max_hourly_rate"],
    }
