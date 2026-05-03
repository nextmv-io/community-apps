import os

import nextmv
import nextmv.cloud
import nextroute.schema as nextrouteSchema
import numpy as np
from nextpipe import FlowSpec, app, needs, step
from traveltimepy import Client
from traveltimepy.requests.common import Coordinates, Location, Property
from traveltimepy.requests.time_filter_fast import TimeFilterFastArrivalSearches, TimeFilterFastOneToMany
from traveltimepy.requests.transportation import TransportationFast


def create_traveltime_client():
    import os

    # Check if API credentials are available
    app_id = os.getenv("TT_APP_ID")
    api_key = os.getenv("TT_API_KEY")

    if not app_id or not api_key:
        raise ValueError(
            "TravelTime API credentials not found. Please set the following environment variables:\n"
            "- TT_APP_ID: Your TravelTime application ID\n"
            "- TT_API_KEY: Your TravelTime API key\n\n"
            "You can get these credentials from: https://docs.traveltime.com/api/overview/getting-keys"
        )

    return Client(app_id=app_id, api_key=api_key)


def build_locations_list(nextroute_input):
    """
    Build locations list from Nextroute input data.

    Args:
        nextroute_input: Parsed Nextroute input schema

    Returns:
        List of TravelTime Location objects
    """
    locations = []

    # Add stops first
    for stop in nextroute_input.stops:
        locations.append(Location(id=stop.id, coords=Coordinates(lat=stop.location.lat, lng=stop.location.lon)))

    # Add vehicle start/end locations for each vehicle
    for vehicle in nextroute_input.vehicles:
        # Add start location
        start_id = f"{vehicle.id}-start"
        locations.append(
            Location(
                id=start_id,
                coords=Coordinates(
                    lat=nextroute_input.defaults.vehicles.start_location.lat,
                    lng=nextroute_input.defaults.vehicles.start_location.lon,
                ),
            )
        )

        # Add end location
        end_id = f"{vehicle.id}-end"
        locations.append(
            Location(
                id=end_id,
                coords=Coordinates(
                    lat=nextroute_input.defaults.vehicles.end_location.lat,
                    lng=nextroute_input.defaults.vehicles.end_location.lon,
                ),
            )
        )

    return locations


def build_travel_matrices(results, location_ids):
    """
    Build travel time and distance matrices from TravelTime API results.

    Args:
        results: TravelTime API response
        location_ids: List of location IDs in matrix order

    Returns:
        Tuple of (duration_matrix, distance_matrix) as numpy arrays
    """
    # Initialize matrices with zeros or infinity where appropriate
    n = len(location_ids)
    duration_matrix = np.full((n, n), np.inf)
    distance_matrix = np.full((n, n), np.inf)

    # Set diagonal elements to 0 (no travel time from a location to itself)
    np.fill_diagonal(duration_matrix, 0)
    np.fill_diagonal(distance_matrix, 0)

    # Process results to fill in the matrix
    for result in results.results:
        origin_id = result.search_id
        origin_idx = location_ids.index(origin_id)

        for location_result in result.locations:
            destination_idx = location_ids.index(location_result.id)
            # Extract travel time and distance
            props = location_result.properties
            duration_matrix[origin_idx][destination_idx] = props.travel_time
            distance_matrix[origin_idx][destination_idx] = props.distance

    return duration_matrix, distance_matrix


def sync_part(input_data: dict, client):
    """
    Calculate travel matrices using TravelTime API client.

    Args:
        input_data: Nextroute input data dictionary
        client: TravelTime API client instance

    Returns:
        Dictionary containing duration_matrix, distance_matrix, and location_ids
    """
    nextroute_input = nextrouteSchema.Input.from_dict(input_data)

    # Build locations list from input data
    locations = build_locations_list(nextroute_input)
    location_ids = [loc.id for loc in locations]

    one_to_many_searches = []
    for origin_id in location_ids:
        # Get all destinations except the origin itself
        destinations = location_ids.copy()
        destinations.remove(origin_id)

        if destinations:  # Only create search if there are destinations
            one_to_many_searches.append(
                TimeFilterFastOneToMany(
                    id=origin_id,
                    departure_location_id=origin_id,
                    arrival_location_ids=destinations,
                    transportation=TransportationFast.DRIVING,
                    travel_time=7200,  # 2 hours maximum
                    properties=[Property.TRAVEL_TIME, Property.DISTANCE],
                )
            )

    # Execute the API call
    results = client.time_filter_fast(
        locations=locations,
        arrival_searches=TimeFilterFastArrivalSearches(one_to_many=one_to_many_searches, many_to_one=[]),
    )

    # Build travel matrices from API results
    duration_matrix, distance_matrix = build_travel_matrices(results, location_ids)

    return {
        "duration_matrix": duration_matrix.tolist(),
        "distance_matrix": distance_matrix.tolist(),
        "location_ids": location_ids,  # Include location IDs for reference
    }


# >>> Workflow definition
class Flow(FlowSpec):
    @step
    def get_durations_distances(input: dict) -> nextrouteSchema.Input:
        """Get distances and durations from TravelTime."""
        with create_traveltime_client() as client:
            results = sync_part(input, client)
        nextroute_input = nextrouteSchema.Input.from_dict(input)
        nextroute_input.duration_matrix = results["duration_matrix"]
        nextroute_input.distance_matrix = results["distance_matrix"]

        # Verify matrix format and specific routes
        location_ids = results["location_ids"]
        nextmv.log(f"Location order in matrix: {location_ids}")

        # Check routes from vehicle start to first few stops
        start_idx = location_ids.index("vehicle-1-start")
        for i in range(3):  # Check first 3 stops
            stop_idx = location_ids.index(f"location-{i + 1}")
            duration = results["duration_matrix"][start_idx][stop_idx]
            distance = results["distance_matrix"][start_idx][stop_idx]
            nextmv.log(f"Vehicle start to location-{i + 1}: {duration} seconds, {distance} meters")

        return nextroute_input.to_dict()

    @app(app_id="travel-time-routing", instance_id="latest")
    @needs(predecessors=[get_durations_distances])
    @step
    def solve():
        """Runs the model."""
        pass


def main():
    # Load input data
    input = nextmv.load()

    nextmv_api_key = os.getenv("NEXTMV_API_KEY")
    if not nextmv_api_key:
        raise ValueError("NEXTMV_API_KEY environment variable not found")
    client = nextmv.cloud.Client(api_key=nextmv_api_key)
    # Run workflow
    flow = Flow("DecisionFlow", input.data)
    flow.run()

    # Write out the result
    nextmv.write(flow.get_result(flow.solve))


if __name__ == "__main__":
    main()
