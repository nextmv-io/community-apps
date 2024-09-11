import functools
import numbers
import time
from typing import Any

import nextmv
import numpy as np
from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
    )

    # Read and prepare the input data.
    input = nextmv.load_local(options=options, path=options.input)
    apply_defaults(input.data)
    validate_input(input.data)
    process_distance_matrix(input.data)
    process_duration_matrix(input.data)

    nextmv.log("Solving routing problem:")
    nextmv.log(f"  - vehicles: {len(input.data.get('vehicles', []))}")
    nextmv.log(f"  - stops: {len(input.data.get('stops', []))}")

    output = solve(input, options)
    nextmv.write_local(output, path=options.output)


def solve(input: nextmv.Input, options: nextmv.Options) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Prepare data.
    speeds = [v["speed"] if "speed" in v else 1 for v in input.data["vehicles"]]
    capacities = [int(round(v["capacity"])) if "capacity" in v else 0 for v in input.data["vehicles"]]
    quantities = [int(round(s["quantity"])) if "quantity" in s else 0 for s in input.data["stops"]]
    quantities += [0] * (len(input.data["vehicles"]) * 2)
    durations = [int(round(s["duration"])) if "duration" in s else 0 for s in input.data["stops"]]
    durations += [0] * (len(input.data["vehicles"]) * 2)
    max_duration_big_m = 365 * 24 * 60 * 60  # 1 year - used to remove the max_duration constraint if not provided
    max_durations = [v["max_duration"] if "max_duration" in v else max_duration_big_m for v in input.data["vehicles"]]
    start_indices = [len(input.data["stops"]) + i * 2 for i in range(len(input.data["vehicles"]))]
    end_indices = [len(input.data["stops"]) + i * 2 + 1 for i in range(len(input.data["vehicles"]))]
    duration_matrix = input.data["duration_matrix"] if "duration_matrix" in input.data else None
    distance_matrix = input.data["distance_matrix"] if "distance_matrix" in input.data else None

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(input.data["stops"]) + 2 * len(input.data["vehicles"]),
        len(input.data["vehicles"]),
        start_indices,
        end_indices,
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Define transit callbacks.
    def distance_matrix_callback(from_index: int, to_index: int, speed: float):
        """Returns the duration between the two nodes based on the distance_matrix."""
        from_node, to_node = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        duration = int(distance_matrix[from_node][to_node] / speed + durations[to_node])
        return duration

    def duration_matrix_callback(from_index: int, to_index: int):
        """Returns the duration between the two nodes based on the duration_matrix."""
        from_node, to_node = manager.IndexToNode(from_index), manager.IndexToNode(to_index)
        duration = duration_matrix[from_node][to_node] + durations[to_node]
        return duration

    # Create and register the duration callback.
    duration_callbacks = [
        duration_matrix_callback
        if "duration_matrix" in input.data
        else functools.partial(distance_matrix_callback, speed=speed)
        for speed in speeds
    ]
    transit_callbacks = [routing.RegisterTransitCallback(callback) for callback in duration_callbacks]
    routing.AddDimensionWithVehicleTransitAndCapacity(
        transit_callbacks,  # transit callback for each vehicle
        0,  # slack
        max_durations,  # vehicle maximum travel durations
        True,  # start cumul to zero
        "Time",  # dimension name
    )
    for i in range(len(input.data["vehicles"])):
        routing.SetArcCostEvaluatorOfVehicle(transit_callbacks[i], i)

    # Define capacity callback.
    def capacity_callback(from_index):
        """Returns the quantity to pickup/dropoff at the node."""
        return quantities[manager.IndexToNode(from_index)]

    # Create and register the capacity callback.
    demand_callback_index = routing.RegisterUnaryTransitCallback(capacity_callback)
    routing.AddDimensionWithVehicleCapacity(
        demand_callback_index,
        0,  # null capacity slack
        capacities,  # vehicle max capacities
        True,  # start cumul at zero
        "Capacity",
    )

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.time_limit.FromSeconds(options.duration)
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
    search_parameters.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.AUTOMATIC

    # Solve the problem.
    start_time = time.time()
    solution = routing.SolveWithParameters(search_parameters)
    end_time = time.time()

    routes = []
    if solution is not None:
        # Determine the routes.
        max_route_duration = 0
        max_stops_in_vehicle = 0
        min_stops_in_vehicle = len(input.data["stops"])
        activated_vehicles = 0
        for vehicle_index in range(len(input.data["vehicles"])):
            # Get the route for the vehicle.
            input_vehicle = input.data["vehicles"][vehicle_index]
            current_index, previous_index = routing.Start(vehicle_index), -1
            route_duration, stop_count = 0, 0
            vehicle_route = []

            # Traverse the route, we use -1 as the end marker.
            while current_index != -1:
                node_index = manager.IndexToNode(current_index)

                # Keep track of the number of stops. We do not count the start and end locations.
                if node_index < len(input.data["stops"]):
                    stop_count += 1

                # Calculate cumulative duration.
                if previous_index > 0:
                    route_duration += routing.GetArcCostForVehicle(
                        previous_index,
                        current_index,
                        vehicle_index,
                    )

                # Add the stop to the route. If it is a start/end location, assemble it on the fly.
                if node_index < len(input.data["stops"]):
                    vehicle_route.append({"stop": input.data["stops"][node_index]})
                else:
                    is_start = (node_index - len(input.data["stops"])) % 2 == 0
                    if is_start and "start_location" in input_vehicle:
                        vehicle_route.append(
                            {
                                "stop": {
                                    "location": input_vehicle["start_location"],
                                    "id": f'{input_vehicle["id"]}_start',
                                }
                            }
                        )
                    elif not is_start and "end_location" in input_vehicle:
                        vehicle_route.append(
                            {
                                "stop": {
                                    "location": input_vehicle["end_location"],
                                    "id": f'{input_vehicle["id"]}_end',
                                }
                            }
                        )

                # Keep traversing the route.
                previous_index = current_index
                if routing.IsEnd(current_index):
                    current_index = -1
                else:
                    current_index = solution.Value(routing.NextVar(current_index))

            route = {
                "id": input_vehicle["id"],
                "route_travel_distance": route_duration,
                "route": vehicle_route,
            }
            routes.append(route)
            max_route_duration = max(route_duration, max_route_duration)
            activated_vehicles += 1
            max_stops_in_vehicle = max(max_stops_in_vehicle, stop_count)
            min_stops_in_vehicle = min(min_stops_in_vehicle, stop_count)

        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=end_time - start_time),
            result=nextmv.ResultStatistics(
                value=solution.ObjectiveValue(),
                custom={
                    "solution_found": True,
                    "activated_vehicles": activated_vehicles,
                    "max_route_duration": max_route_duration,
                    "max_stops_in_vehicle": max_stops_in_vehicle,
                    "min_stops_in_vehicle": min_stops_in_vehicle,
                },
            ),
        )
    else:
        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=end_time - start_time),
            result=nextmv.ResultStatistics(
                value=None,
                custom={
                    "solution_found": False,
                },
            ),
        )

    return nextmv.Output(
        options=options,
        solution={"vehicles": routes, "unplanned": []},
        statistics=statistics,
    )


def apply_defaults(input_data: dict[str, Any]) -> None:
    """
    Applies default values to the vehicles and stops
    (if they are given and not already set on them directly).
    """
    if "defaults" not in input_data:
        return input_data
    defaults = input_data["defaults"]
    if "vehicles" in defaults:
        for vehicle in input_data["vehicles"]:
            for key, value in defaults["vehicles"].items():
                if key not in vehicle:
                    vehicle[key] = value
    if "stops" in defaults:
        for stop in input_data["stops"]:
            for key, value in defaults["stops"].items():
                if key not in stop:
                    stop[key] = value


def check_valid_location(element: dict[str, Any]) -> bool:
    """Checks if the given element is a valid location."""
    if (
        "lon" not in element
        or not isinstance(element["lon"], numbers.Number)
        or element["lon"] < -180
        or element["lon"] > 180
    ):
        return False
    if (
        "lat" not in element
        or not isinstance(element["lat"], numbers.Number)
        or element["lat"] < -90
        or element["lat"] > 90
    ):
        return False
    return True


def validate_matrix(matrix: list[list[float]], input_data: dict[str, Any], matrix_type: str) -> None:
    n_stops, n_vehicles = len(input_data["stops"]), len(input_data["vehicles"])
    dim_stops, dim_full = n_stops, n_stops + 2 * n_vehicles
    # Make sure the matrix is square.
    if not all(len(row) == len(matrix) for row in matrix):
        raise ValueError(f"{matrix_type} is not square.")
    # Accept the matrix if it is full (all stops and vehicle start/end locations covered).
    if len(matrix) == dim_full:
        return
    # Only accept a matrix that covers only the stops if no vehicle start/end locations are given.
    if len(matrix) == dim_stops:
        if any("start_location" in vehicle or "end_location" in vehicle for vehicle in input_data["vehicles"]):
            raise ValueError(f"{matrix_type} does not cover all vehicle start/end locations.")
        return
    # Otherwise, the matrix is invalid.
    raise ValueError(
        f"{matrix_type} is of invalid size. "
        + "A full matrix has the following shape: "
        + "[stop_1, ..., stop_n, vehicle_1_start, vehicle_1_end, ..., vehicle_n_start, vehicle_n_end]."
    )


def validate_input(input_data: dict[str, Any]) -> None:
    """
    Runs basic checks on the input data to ensure it is valid.
    """
    if len(input_data.get("vehicles", [])) == 0:
        raise ValueError("No vehicles provided.")
    if len(input_data.get("stops", [])) == 0:
        raise ValueError("No stops provided.")
    if "distance_matrix" in input_data:
        validate_matrix(input_data["distance_matrix"], input_data, "distance_matrix")
    if "duration_matrix" in input_data:
        validate_matrix(input_data["duration_matrix"], input_data, "duration_matrix")
    for vehicle in input_data["vehicles"]:
        if "id" not in vehicle:
            raise ValueError(f"Vehicle {vehicle} does not have an id.")
        ident = vehicle["id"]
        if "capacity" in vehicle and (not isinstance(vehicle["capacity"], numbers.Integral) or vehicle["capacity"] < 0):
            raise ValueError(f"Invalid capacity {vehicle['capacity']} for vehicle {ident}.")
        if "start_location" in vehicle and not check_valid_location(vehicle["start_location"]):
            raise ValueError(f"Invalid start_location {vehicle['start_location']} for vehicle {ident}.")
        if "end_location" in vehicle and not check_valid_location(vehicle["end_location"]):
            raise ValueError(f"Invalid end_location {vehicle['end_location']} for vehicle {ident}.")
        if "speed" in vehicle and (not isinstance(vehicle["speed"], numbers.Number) or vehicle["speed"] <= 0):
            raise ValueError(f"Invalid speed {vehicle['speed'] if 'speed' in vehicle else None} for vehicle {ident}.")
        if "max_duration" in vehicle and (
            not isinstance(vehicle["max_duration"], numbers.Number) or vehicle["max_duration"] < 0
        ):
            raise ValueError(f"Invalid max_duration {vehicle['max_duration']} for vehicle {ident}.")
    for stop in input_data["stops"]:
        if "id" not in stop:
            raise ValueError(f"Stop {stop} does not have an id.")
        ident = stop["id"]
        if "location" not in stop or not check_valid_location(stop["location"]):
            raise ValueError(f"Invalid location {stop['location'] if 'location' in stop else None} for stop {ident}.")
        if "duration" in stop and (not isinstance(stop["duration"], numbers.Number) or stop["duration"] < 0):
            raise ValueError(f"Invalid duration {stop['duration']} for stop {ident}.")
        if "quantity" in stop and (not isinstance(stop["quantity"], numbers.Integral) or stop["quantity"] < 0):
            raise ValueError(f"Invalid quantity {stop['quantity']} for stop {ident}.")
    if "duration_matrix" not in input_data and not all("speed" in vehicle for vehicle in input_data["vehicles"]):
        raise ValueError("Speed missing and no duration matrix provided. At least one of them is required.")


def expand_missing_start_end(matrix: np.ndarray, input_data: dict[str, Any]) -> np.ndarray:
    """
    Expands the given matrix with 0s for the start and end locations.
    """
    n_stops, n_vehicles = len(input_data["stops"]), len(input_data["vehicles"])
    if len(matrix) == n_stops + 2 * n_vehicles:
        return matrix  # No expansion needed
    expanded_matrix = np.zeros((n_stops + 2 * n_vehicles, n_stops + 2 * n_vehicles))
    expanded_matrix[:n_stops, :n_stops] = matrix
    return expanded_matrix


def calculate_distance_matrix(input_data: dict[str, Any]) -> np.ndarray:
    """
    Calculates the distance matrix for the input data.
    """
    # Otherwise, calculate the distance matrix from the locations using the haversine formula.
    start = time.time()
    lats_origin = np.array([s["location"]["lat"] for s in input_data["stops"]])
    for vehicle in input_data["vehicles"]:
        lats_origin = np.append(lats_origin, vehicle["start_location"]["lat"])
        lats_origin = np.append(lats_origin, vehicle["end_location"]["lat"])
    lons_origin = np.array([s["location"]["lon"] for s in input_data["stops"]])
    for vehicle in input_data["vehicles"]:
        lons_origin = np.append(lons_origin, vehicle["start_location"]["lon"])
        lons_origin = np.append(lons_origin, vehicle["end_location"]["lon"])
    lats_destination = np.copy(lats_origin)
    lons_destination = np.copy(lons_origin)

    # Create the combination of all origins and destinations.
    lats_origin = np.repeat(lats_origin, len(lats_destination))
    lons_origin = np.repeat(lons_origin, len(lons_destination))
    lats_destination = np.tile(lats_destination, len(lats_destination))
    lons_destination = np.tile(lons_destination, len(lons_destination))

    distances = haversine(
        lats_origin=lats_origin,
        lons_origin=lons_origin,
        lats_destination=lats_destination,
        lons_destination=lons_destination,
    )

    # Convert the distances to a square matrix.
    num_locations = len(input_data["stops"]) + 2 * len(input_data["vehicles"])
    matrix = distances.reshape(num_locations, num_locations)

    end = time.time()
    nextmv.log(f"Distance matrix calculation took {round(end - start, 2)} seconds.")
    return matrix


def process_distance_matrix(input_data: dict[str, Any]) -> None:
    """Calculates the distance matrix for the input data."""

    # If the input data already contains a distance matrix, return it.
    if "distance_matrix" in input_data:
        np_matrix = np.array(input_data["distance_matrix"])
        input_data["distance_matrix"] = expand_missing_start_end(np_matrix, input_data)

    # Only calculate the distance matrix if there is no duration matrix.
    if "duration_matrix" not in input_data and "distance_matrix" not in input_data:
        input_data["distance_matrix"] = calculate_distance_matrix(input_data)

    # Make sure the matrix is integer (round the values).
    if "distance_matrix" in input_data:
        input_data["distance_matrix"] = np.rint(input_data["distance_matrix"]).astype(int)


def process_duration_matrix(input_data: dict[str, Any]) -> None:
    """Prepares the duration matrix of the input data, if given."""

    # If the input data already contains a duration matrix, return it.
    if "duration_matrix" in input_data:
        np_matrix = np.array(input_data["duration_matrix"])
        input_data["duration_matrix"] = expand_missing_start_end(np_matrix, input_data)

    # Make sure the matrix is integer (round the values).
    if "duration_matrix" in input_data:
        input_data["duration_matrix"] = np.rint(input_data["duration_matrix"]).astype(int)


def haversine(
    lats_origin: np.ndarray | float,
    lons_origin: np.ndarray | float,
    lats_destination: np.ndarray | float,
    lons_destination: np.ndarray | float,
) -> np.ndarray | float:
    """Calculates the haversine distance between arrays of coordinates."""

    lons_destination, lats_destination, lons_origin, lats_origin = map(
        np.radians,
        [lons_destination, lats_destination, lons_origin, lats_origin],
    )
    delta_lon = lons_destination - lons_origin
    delta_lat = lats_destination - lats_origin
    term1 = np.sin(delta_lat / 2.0) ** 2
    term2 = np.cos(lats_origin) * np.cos(lats_destination) * np.sin(delta_lon / 2.0) ** 2
    a = term1 + term2
    c = 2 * np.arcsin(np.sqrt(a))
    earth_radius = 6371000

    return earth_radius * c


if __name__ == "__main__":
    main()
