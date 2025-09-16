# test_distance_calculator.py

from math import radians, sin, cos, sqrt, atan2


def calculate_distance(point1: dict, point2: dict) -> float:
    R = 6371  # Earth's radius in kilometers

    # Extract latitude and longitude from point1 (seeker's location)
    lat1 = float(point1.get("latitude", 0))
    lon1 = float(point1.get("longitude", 0))

    # Extract latitude and longitude from point2 (job location)
    if "coordinates" in point2 and isinstance(point2["coordinates"], list):
        # GeoJSON Point format
        lon2, lat2 = map(float, point2["coordinates"])
    else:
        # Regular lat/lng format
        lat2 = float(point2.get("latitude", 0))
        lon2 = float(point2.get("longitude", 0))

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    distance = R * c
    return distance


def test_distance_calculation():
    # point1 = {'latitude': 12.9719, 'longitude': 77.6412}
    # point2 = {'coordinates': [77.6412, 12.9719], 'type': 'Point'}
    point1 = {"latitude": 28.587287673028868, "longitude": 77.44188595901245}
    point2 = {"coordinates": [77.4363720047502, 28.593887491569742], "type": "Point"}
    distance = calculate_distance(point1, point2)
    print(f"Calculated distance: {distance:.6f} km")

    if distance < 0.1:  # Less than 100 meters
        print(
            "Test passed: Distance is very small as expected for identical coordinates."
        )
    else:
        print(
            "Test failed: Distance is larger than expected for identical coordinates."
        )


if __name__ == "__main__":
    test_distance_calculation()
