import json

from shapely.geometry import Polygon


def load_zones(json_path):
    """Loads polygon zones from a JSON file."""
    with open(json_path, "r") as f:
        data = json.load(f)
    red_zone = Polygon(data["red_zone"])
    green_zone = Polygon(data["green_zone"])
    return red_zone, green_zone
