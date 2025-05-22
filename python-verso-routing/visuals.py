import json
from typing import Dict, List, Any
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
    def hsl_to_rgb(h: float, s: float = 0.7, l: float = 0.5) -> str:
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

        q = l * (1 + s) if l < 0.5 else l + s - l * s
        p = 2 * l - q
        
        r = hue_to_rgb(p, q, h + 1/3)
        g = hue_to_rgb(p, q, h)
        b = hue_to_rgb(p, q, h - 1/3)
        
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"
    
    return hsl_to_rgb(hue)

def create_visuals(solution: Dict[str, Any]) -> Asset:
    """
    Creates a GeoJSON visualization from the routes in the solution.
    Includes both route lines and step points.
    
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
        
        # Get coordinates from steps
        coordinates = []
        for step in route.get("steps", []):
            if "location" in step:
                # Convert [lng, lat] to [lat, lng] for Leaflet
                lng, lat = step["location"]
                coordinates.append([lng, lat])
                
                # Create point feature for each step
                point_feature = {
                    "type": "Feature",
                    "properties": {
                        "metadata": [
                            {"key": "Vehicle", "value": f"Vehicle {vehicle_id}"},
                            {"key": "Type", "value": step.get("type", "")},
                            {"key": "Description", "value": step.get("description", "")},
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
                        "coordinates": [lng, lat]  # Leaflet format
                    }
                }
                features.append(point_feature)
        
        # Create line feature for the route
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
                    "opacity": 0.7
                }
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coordinates  # Already converted to [lat, lng]
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
        content_type="json",
        visual={
            "schema": "geojson",
            "label": "Route Visualization",
            "type": "custom-tab"
        }
    ) 