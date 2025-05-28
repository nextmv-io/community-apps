import asyncio

import nextmv
import nextroute.schema as nextrouteSchema
import numpy as np
from nextpipe import FlowSpec, app, needs, step
from traveltimepy import Coordinates, Location, Property, Transportation, TravelTimeSdk


async def async_part(input_data: dict):
    sdk = TravelTimeSdk(app_id="TT_APP_ID", api_key="TT_API_KEY")
    nextroute_input = nextrouteSchema.Input.from_dict(input_data)
    # Create locations for all stops
    locations = []
    location_ids = []

    # Add stops first
    for stop in nextroute_input.stops:
        locations.append(
            Location(
                id=stop.id,
                coords=Coordinates(lat=stop.location.lat, lng=stop.location.lon)
            )
        )
        location_ids.append(stop.id)

    # Add vehicle start/end locations for each vehicle
    for vehicle in nextroute_input.vehicles:
        # Add start location
        start_id = f"{vehicle.id}-start"
        locations.append(
            Location(
                id=start_id,
                coords=Coordinates(
                    lat=nextroute_input.defaults.vehicles.start_location.lat,
                    lng=nextroute_input.defaults.vehicles.start_location.lon
                )
            )
        )
        location_ids.append(start_id)

        # Add end location
        end_id = f"{vehicle.id}-end"
        locations.append(
            Location(
                id=end_id,
                coords=Coordinates(
                    lat=nextroute_input.defaults.vehicles.end_location.lat,
                    lng=nextroute_input.defaults.vehicles.end_location.lon
                )
            )
        )
        location_ids.append(end_id)

    # Prepare the search_ids dictionary - each location to all other locations
    search_ids = {}
    for origin in location_ids:
        # Each origin should search for all destinations except itself
        search_ids[origin] = [dest for dest in location_ids if dest != origin]

    # Execute the API call
    results = await sdk.time_filter_fast_async(
        locations=locations,
        search_ids=search_ids,
        transportation=Transportation(type="driving"),
        properties=[Property("distance"), Property("travel_time")],
        one_to_many=False,
    )

    # Initialize matrices with zeros or infinity where appropriate
    n = len(location_ids)
    duration_matrix = np.full((n, n), np.inf)
    distance_matrix = np.full((n, n), np.inf)

    # Set diagonal elements to 0 (no travel time from a location to itself)
    np.fill_diagonal(duration_matrix, 0)
    np.fill_diagonal(distance_matrix, 0)

    # Process results to fill in the matrix
    for result in results:
        origin_idx = location_ids.index(result.search_id)

        for location in result.locations:
            destination_idx = location_ids.index(location.id)
            # Convert travel time to seconds if needed
            duration_matrix[origin_idx][destination_idx] = location.properties.travel_time
            distance_matrix[origin_idx][destination_idx] = location.properties.distance

    # Convert numpy arrays to lists for JSON serialization
    duration_matrix_list = duration_matrix.tolist()
    distance_matrix_list = distance_matrix.tolist()

    return {
        "duration_matrix": duration_matrix_list,
        "distance_matrix": distance_matrix_list,
        "location_ids": location_ids  # Include location IDs for reference
    }

# >>> Workflow definition
class Flow(FlowSpec):
    @step
    def get_durations_distances(input: dict) -> nextrouteSchema.Input:
        """Get distances and durations from TravelTime."""
        results = asyncio.run(async_part(input))
        nextroute_input = nextrouteSchema.Input.from_dict(input)
        nextroute_input.duration_matrix = results["duration_matrix"]
        nextroute_input.distance_matrix = results["distance_matrix"]

        # Verify matrix format and specific routes
        location_ids = results["location_ids"]
        nextmv.log(f"Location order in matrix: {location_ids}")

        # Check routes from vehicle start to first few stops
        start_idx = location_ids.index("vehicle-1-start")
        for i in range(3):  # Check first 3 stops
            stop_idx = location_ids.index(f"location-{i+1}")
            duration = results["duration_matrix"][start_idx][stop_idx]
            distance = results["distance_matrix"][start_idx][stop_idx]
            nextmv.log(f"Vehicle start to location-{i+1}: {duration} seconds, {distance} meters")

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

    # Run workflow
    flow = Flow("DecisionFlow", input.data)
    flow.run()

    # Write out the result
    nextmv.write(flow.get_result(flow.solve))


if __name__ == "__main__":
    main()
