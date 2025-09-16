import requests

# Google Maps API Key (Replace with your actual API key)
GOOGLE_MAPS_API_KEY = "AIzaSyCl7gQBLcKtKZpph03jOIDGajfp41wdw2k"


def get_address_from_lat_lon(latitude: float, longitude: float):
    """
    Fetches address details using Google Maps API based on latitude and longitude.
    """
    try:
        url = "https://maps.googleapis.com/maps/api/geocode/json"
        params = {"latlng": f"{latitude},{longitude}", "key": GOOGLE_MAPS_API_KEY}
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()

        if data["status"] == "OK":
            address_components = data["results"][0]["address_components"]
            formatted_address = data["results"][0]["formatted_address"]

            # Extracting locality, state, country, and postal code
            address_details = {
                "formatted_address": formatted_address,
                "locality": None,
                "state": None,
                "country": None,
                "postal_code": None,
            }

            for component in address_components:
                types = component["types"]
                if "locality" in types:
                    address_details["locality"] = component["long_name"]
                if "administrative_area_level_1" in types:
                    address_details["state"] = component["long_name"]
                if "country" in types:
                    address_details["country"] = component["long_name"]
                if "postal_code" in types:
                    address_details["postal_code"] = component["long_name"]

            return address_details
        else:
            return {"error": "No results found for the given coordinates."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Request failed: {str(e)}"}


if __name__ == "__main__":
    print("\n📍 Enter Latitude and Longitude to get the address\n")
    latitude = float(input("Enter Latitude: "))
    longitude = float(input("Enter Longitude: "))

    address_info = get_address_from_lat_lon(latitude, longitude)

    if "error" in address_info:
        print(f"\n❌ Error: {address_info['error']}")
    else:
        print("\n📍 Address Details:")
        print(f"🗺 Formatted Address: {address_info['formatted_address']}")
        print(f"🏙 Locality: {address_info['locality']}")
        print(f"🌍 State: {address_info['state']}")
        print(f"🌎 Country: {address_info['country']}")
        print(f"📮 Postal Code: {address_info['postal_code']}")
