import nextmv
from colour import Color


def create_visual(data, solution_routes):
    """Creates a GeoJSON visualization from a cuOpt solution."""
    features = []

    # Build location lookup: index -> coordinates
    location_coords = {}
    location_metadata = {}

    # Add vehicle starts
    for i, v in enumerate(data["vehicles"]):
        location_coords[i] = v["start"]
        location_metadata[i] = {"type": "Depot", "description": f"Vehicle {v['id']} Start"}

    # Add jobs
    job_start_idx = len(data["vehicles"])
    for i, job in enumerate(data["jobs"]):
        location_coords[job_start_idx + i] = job["location"]
        location_metadata[job_start_idx + i] = {
            "type": "Delivery",
            "description": job.get("description", ""),
            "id": job.get("id", ""),
        }

    # Add vehicle ends
    vehicle_end_start_idx = job_start_idx + len(data["jobs"])
    for i, v in enumerate(data["vehicles"]):
        location_coords[vehicle_end_start_idx + i] = v["end"]
        location_metadata[vehicle_end_start_idx + i] = {"type": "Depot", "description": f"Vehicle {v['id']} End"}

    # Group routes by vehicle
    routes_by_vehicle = {}
    for route in solution_routes:
        truck_id = route["truck_id"]
        if truck_id not in routes_by_vehicle:
            routes_by_vehicle[truck_id] = []
        routes_by_vehicle[truck_id].append(route)

    # Routes are already in correct sequence order from cuOpt
    # Do NOT sort by 'route' field - that's the location index, not sequence!

    # Create features for each vehicle
    for truck_id, routes in sorted(routes_by_vehicle.items()):
        color = Color(pick_for=truck_id).hex

        # Create points for each stop
        for route in routes:
            location_idx = route["location"]
            if location_idx in location_coords:
                coords = location_coords[location_idx]
                metadata = location_metadata.get(location_idx, {})

                point_feature = {
                    "type": "Feature",
                    "properties": {
                        "metadata": [
                            {"key": "Vehicle", "value": f"Vehicle {truck_id}"},
                            {"key": "Type", "value": metadata.get("type", route.get("type", ""))},
                            {"key": "Description", "value": metadata.get("description", "")},
                            {"key": "ID", "value": metadata.get("id", "")},
                            {"key": "Arrival Time", "value": f"{route['arrival_stamp']:.2f}"},
                            {"key": "Sequence", "value": route["route"]},
                        ],
                        "style": {"fillColor": color, "fillOpacity": 0.7, "radius": 8, "weight": 2, "opacity": 1},
                    },
                    "geometry": {
                        "type": "Point",
                        "coordinates": coords,  # [lng, lat]
                    },
                }
                features.append(point_feature)

        # Create line for the route
        route_coordinates = []
        for route in routes:
            location_idx = route["location"]
            if location_idx in location_coords:
                route_coordinates.append(location_coords[location_idx])

        if len(route_coordinates) > 1:
            line_feature = {
                "type": "Feature",
                "properties": {
                    "metadata": [
                        {"key": "Vehicle", "value": f"Vehicle {truck_id}"},
                        {"key": "Stops", "value": len(routes)},
                        {"key": "Total Time", "value": f"{routes[-1]['arrival_stamp']:.2f}"},
                    ],
                    "style": {"color": color, "weight": 3, "opacity": 0.7, "lineCap": "round", "lineJoin": "round"},
                },
                "geometry": {"type": "LineString", "coordinates": route_coordinates},
            }
            features.append(line_feature)

    # Create GeoJSON FeatureCollection
    geojson = {"type": "FeatureCollection", "features": features}

    # Create and return Nextmv Asset
    return nextmv.Asset(
        name="Route Visualization",
        content=geojson,
        visual={"schema": "geojson", "label": "Route Visualization", "type": "custom-tab"},
    )
