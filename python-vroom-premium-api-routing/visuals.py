import math
from typing import Any

import polyline
from nextmv import Asset


def generate_color(index: int, total: int) -> str:
    """
    Generates a color from a continuous color spectrum based on index and total count.
    Uses HSL color space to ensure good color separation.

    Args:
        index: The index of the vehicle (0-based)
        total: Total number of vehicles

    Returns:
        str: Hex color code
    """
    # Use golden ratio to get well-distributed hues
    golden_ratio = 0.618033988749895
    hue = (index * golden_ratio) % 1.0

    # Convert HSL to RGB
    def hsl_to_rgb(hue: float, saturation: float = 0.7, lightness: float = 0.5) -> str:
        def hue_to_rgb(p: float, q: float, t: float) -> float:
            if t < 0:
                t += 1
            if t > 1:
                t -= 1
            if t < 1/6:
                return p + (q - p) * 6 * t
            if t < 1/2:
                return q
            if t < 2/3:
                return p + (q - p) * (2/3 - t) * 6
            return p

        q = lightness * (1 + saturation) if lightness < 0.5 else lightness + saturation - lightness * saturation
        p = 2 * lightness - q

        r = hue_to_rgb(p, q, hue + 1/3)
        g = hue_to_rgb(p, q, hue)
        b = hue_to_rgb(p, q, hue - 1/3)

        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    return hsl_to_rgb(hue)

def get_arrow_coordinates(start: list[float], end: list[float], fraction: float = 0.5) -> tuple[list[float], float]:
    """
    Calculate the position and bearing of an arrow between two points.

    Args:
        start: Start coordinates [lng, lat]
        end: End coordinates [lng, lat]
        fraction: Position along the line (0-1)

    Returns:
        tuple: (arrow position [lng, lat], bearing in degrees)
    """
    # Calculate position
    lng = start[0] + (end[0] - start[0]) * fraction
    lat = start[1] + (end[1] - start[1]) * fraction

    # Calculate bearing
    d_lng = end[0] - start[0]
    d_lat = end[1] - start[1]
    bearing = math.degrees(math.atan2(d_lng, d_lat))

    return [lng, lat], bearing

def create_visuals(solution: dict[str, Any]) -> Asset:
    """
    Creates a GeoJSON visualization from the routes in the solution.
    Includes route lines and step points.

    Args:
        solution: The solution dictionary containing route information

    Returns:
        Asset: A Nextmv Asset containing the GeoJSON visualization
    """
    features = []

    # Extract routes directly from solution
    routes = solution.get("routes", [])
    total_routes = len(routes)

    for i, route in enumerate(routes):
        vehicle_id = route.get("vehicle")
        route_color = generate_color(i, total_routes)

        # Get coordinates from steps for points
        step_coordinates = []
        for step in route.get("steps", []):
            if "location" in step:
                lng, lat = step["location"]
                step_coordinates.append([lng, lat])

                # Create point feature for each step
                point_feature = {
                    "type": "Feature",
                    "properties": {
                        "metadata": [
                            {"key": "Vehicle", "value": f"Vehicle {vehicle_id}"},
                            {"key": "Type", "value": step.get("type", "")},
                            {"key": "Description", "value": step.get("description", "")},
                            {"key": "ID", "value": step.get("id", "N/A")},
                            {"key": "Distance (m)", "value": step.get("distance", 0)},
                            {"key": "Arrival (s)", "value": step.get("arrival", 0)},
                            {"key": "Duration (s)", "value": step.get("duration", 0)}
                        ],
                        "style": {
                            "fillColor": route_color,
                            "fillOpacity": 0.7,
                            "radius": 8,
                            "weight": 2,
                            "opacity": 1
                        }
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": [lng, lat]  # Leaflet format [lng, lat]
                    }
                }
                features.append(point_feature)

        # Create line feature for the route using the geometry field
        if "geometry" in route:
            # Decode the polyline geometry to get coordinates
            route_coordinates = polyline.decode(route["geometry"])
            # Convert [lat, lng] to [lng, lat] for Leaflet
            route_coordinates = [[lng, lat] for lat, lng in route_coordinates]

            line_feature = {
                "type": "Feature",
                "properties": {
                    "metadata": [
                        {"key": "Vehicle", "value": f"Vehicle {vehicle_id}"},
                        {"key": "Cost", "value": route.get("cost", 0)},
                        {"key": "Distance (m)", "value": route.get("distance", 0)},
                        {"key": "Duration (s)", "value": route.get("duration", 0)}
                    ],
                    "style": {
                        "color": route_color,
                        "weight": 3,
                        "opacity": 0.7,
                        "lineCap": "round",
                        "lineJoin": "round"
                    }
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": route_coordinates  # Leaflet format [lng, lat]
                }
            }
            features.append(line_feature)

    # Create GeoJSON FeatureCollection
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }

    # Create and return Nextmv Asset
    return Asset(
        name="Route Visualization",
        content=geojson,
        visual={
            "label": "Route Visualization",
            "schema": "geojson",
            "type": "output-visual"
        }
    )
