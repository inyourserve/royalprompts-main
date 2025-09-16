from math import radians, sin, cos, sqrt, atan2
from typing import Dict, Any


def calculate_distance(point1: Dict[str, Any], point2: Dict[str, Any]) -> float:
    """
    Calculate the distance between two points using the Haversine formula.

    Args:
        point1: Dict containing latitude and longitude of first point
        point2: Dict containing coordinates or latitude/longitude of second point

    Returns:
        float: Distance in meters
    """
    R = 6371  # Earth's radius in kilometers

    # Extract coordinates from point1 (seeker's location)
    lat1 = float(point1.get("latitude", 0))
    lon1 = float(point1.get("longitude", 0))

    # Extract coordinates from point2 (job location)
    if "coordinates" in point2 and isinstance(point2["coordinates"], list):
        # GeoJSON Point format: [longitude, latitude]
        lon2, lat2 = map(float, point2["coordinates"])
    else:
        lat2 = float(point2.get("latitude", 0))
        lon2 = float(point2.get("longitude", 0))

    # Validate coordinates
    if not all([lat1, lon1, lat2, lon2]):
        raise ValueError("Invalid coordinates: missing or zero values")

    # Convert to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c

    return distance * 1000  # Convert to meters


def estimate_time(distance: float) -> int:
    """
    Estimate travel time based on distance.

    Args:
        distance: Distance in meters

    Returns:
        int: Estimated time in minutes
    """
    speed = 8.33333  # meters/second (30 km/h)
    time_seconds = distance / speed
    return max(1, int(time_seconds / 60))  # Minimum 1 minute
