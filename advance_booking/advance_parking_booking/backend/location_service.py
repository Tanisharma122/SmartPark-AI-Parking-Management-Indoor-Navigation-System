from geopy.geocoders import Nominatim
from geopy.distance import geodesic

# Initialize Geolocator with a custom user-agent (Required by OSM)
geolocator = Nominatim(user_agent="smart_parking_app")

def get_coordinates(place_name):
    """
    Convert a place name to (latitude, longitude).
    Appends ', Ahmedabad, India' for better accuracy if not present.
    """
    try:
        search_query = place_name
        if "Ahmedabad" not in place_name and "India" not in place_name:
            search_query += ", Ahmedabad, Gujarat, India"
            
        location = geolocator.geocode(search_query)
        if location:
            return (location.latitude, location.longitude)
        return None
    except Exception as e:
        print(f"Geocoding Error: {e}")
        return None

def calculate_distance(coords1, coords2):
    """
    Calculate distance in Kilometers between two points.
    """
    return geodesic(coords1, coords2).km
