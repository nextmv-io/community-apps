import numbers
import time
from typing import Any

import nextmv
import numpy as np
from pyvrp import Model
from pyvrp.stop import MaxRuntime


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Option("duration", int, 30, "Max runtime duration (in seconds).", False),
    )

    # Read and prepare the input data.
    input = nextmv.load(options=options, path=options.input)
    apply_defaults(input.data)
    validate_input(input.data)
    process_distance_matrix(input.data)
    process_duration_matrix(input.data)

    nextmv.log("Solving routing problem:")
    nextmv.log(f"  - vehicles: {len(input.data.get('vehicles', []))}")
    nextmv.log(f"  - stops: {len(input.data.get('stops', []))}")

    model = DecisionModel()
    output = model.solve(input, options.duration)
    nextmv.write(output, path=options.output)


class DecisionModel(nextmv.Model):
    def solve(self, input: nextmv.Input, duration: int) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        start_time = time.time()
        nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

        vehicles = input.data["vehicles"]
        stops = input.data["stops"]
        n_vehicles = len(vehicles)
        n_stops = len(stops)

        # Prepare data arrays.
        capacities = [int(round(v["capacity"])) if "capacity" in v else 0 for v in vehicles]
        quantities = [int(round(s["quantity"])) if "quantity" in s else 0 for s in stops]
        service_durations = [int(round(s["duration"])) if "duration" in s else 0 for s in stops]
        max_duration_big_m = 365 * 24 * 60 * 60  # 1 year
        max_durations = [v["max_duration"] if "max_duration" in v else max_duration_big_m for v in vehicles]
        speeds = [v["speed"] if "speed" in v else 1 for v in vehicles]

        # Determine which matrix to use for travel costs.
        # Input matrix layout:
        # [stop_0, ..., stop_{n-1}, v0_start, v0_end, v1_start, v1_end, ...]
        # PyVRP location layout:
        # [v0_start_depot, v0_end_depot, v1_start_depot, v1_end_depot, ..., client_0, ..., client_{n-1}]
        # We need to map between these two orderings.
        use_duration_matrix = "duration_matrix" in input.data
        if use_duration_matrix:
            distance_matrix = input.data["duration_matrix"]  # use as both distance and duration
        else:
            distance_matrix = input.data["distance_matrix"]

        # Map: pyvrp location index -> input matrix index
        # PyVRP depot indices (in add order): v_i_start = 2*i, v_i_end = 2*i+1
        # PyVRP client indices: 2*n_vehicles + j  for stop j
        # Input matrix: stop j = j, v_i_start = n_stops + 2*i, v_i_end = n_stops + 2*i + 1
        def pyvrp_to_matrix_idx(pyvrp_idx: int) -> int:
            if pyvrp_idx < 2 * n_vehicles:
                # It's a depot: vehicle i, start/end
                vehicle_i = pyvrp_idx // 2
                is_start = (pyvrp_idx % 2) == 0
                return n_stops + vehicle_i * 2 + (0 if is_start else 1)
            else:
                # It's a client (stop)
                stop_j = pyvrp_idx - 2 * n_vehicles
                return stop_j

        # Build the PyVRP model.
        m = Model()

        # Add depots (start and end location for each vehicle).
        # We use dummy (0,0) coordinates since we provide an explicit matrix.
        depots = []
        for vehicle in vehicles:
            start_depot = m.add_depot(x=0, y=0, name=f"{vehicle['id']}_start")
            end_depot = m.add_depot(x=0, y=0, name=f"{vehicle['id']}_end")
            depots.append((start_depot, end_depot))

        # Add clients (stops).
        clients = []
        for j, stop in enumerate(stops):
            client = m.add_client(
                x=0,
                y=0,
                delivery=quantities[j],
                service_duration=service_durations[j],
                name=stop["id"],
            )
            clients.append(client)

        # When using a distance matrix + speed, we need per-vehicle routing profiles
        # so that edge durations = distance / speed can differ per vehicle.
        # When using a duration matrix, one profile with duration=travel time suffices.
        if use_duration_matrix:
            profiles = [None]  # single default profile
        else:
            profiles = [m.add_profile(name=vehicle["id"]) for vehicle in vehicles]

        # Add vehicle types (one per vehicle, num_available=1).
        for i, vehicle in enumerate(vehicles):
            start_depot, end_depot = depots[i]
            profile = profiles[0] if use_duration_matrix else profiles[i]
            m.add_vehicle_type(
                num_available=1,
                capacity=capacities[i],
                start_depot=start_depot,
                end_depot=end_depot,
                shift_duration=max_durations[i],
                unit_distance_cost=0,
                unit_duration_cost=1,
                profile=profile,
                name=vehicle["id"],
            )

        # Add edges using the travel matrix.
        # We add edges between all pairs of PyVRP locations.
        all_locations = m.locations  # depots first, then clients
        n_locations = len(all_locations)  # 2*n_vehicles + n_stops

        for from_pyvrp_idx in range(n_locations):
            from_mat_idx = pyvrp_to_matrix_idx(from_pyvrp_idx)
            for to_pyvrp_idx in range(n_locations):
                to_mat_idx = pyvrp_to_matrix_idx(to_pyvrp_idx)
                dist = int(distance_matrix[from_mat_idx][to_mat_idx])
                if use_duration_matrix:
                    # duration matrix: distance and duration are both the travel time value
                    m.add_edge(
                        all_locations[from_pyvrp_idx],
                        all_locations[to_pyvrp_idx],
                        distance=dist,
                        duration=dist,
                    )
                else:
                    # distance matrix + per-vehicle speed: add one edge per profile
                    # with duration = distance / speed (integer)
                    for i, speed in enumerate(speeds):
                        dur = int(dist / speed)
                        m.add_edge(
                            all_locations[from_pyvrp_idx],
                            all_locations[to_pyvrp_idx],
                            distance=dist,
                            duration=dur,
                            profile=profiles[i],
                        )

        # Solve the problem.
        start_time = time.time()
        result = m.solve(stop=MaxRuntime(duration), display=False)
        end_time = time.time()

        routes = []
        if result.is_feasible():
            best = result.best

            # Build a map from vehicle type index to vehicle data.
            max_route_duration = 0
            max_stops_in_vehicle = 0
            min_stops_in_vehicle = n_stops
            activated_vehicles = 0
            planned_stop_ids = set()

            # Build per-vehicle route lists (indexed by vehicle index).
            vehicle_routes: dict[str, list] = {}
            for vehicle in vehicles:
                vehicle_routes[vehicle["id"]] = []

            for route in best.routes():
                vt_idx = route.vehicle_type()
                vehicle = vehicles[vt_idx]
                vehicle_id = vehicle["id"]
                vehicle_route = []

                # Add start location if vehicle has one.
                if "start_location" in vehicle:
                    vehicle_route.append(
                        {
                            "stop": {
                                "id": f"{vehicle_id}_start",
                                "location": vehicle["start_location"],
                            },
                            "type": "start",
                            "arrival": 0,
                            "duration": 0,
                            "setup": 0,
                            "service": 0,
                            "waiting_time": 0,
                        }
                    )

                # Get scheduled visits for the route.
                # schedule() includes depot visits: [start_depot, client_0, ..., client_n, end_depot]
                schedule = route.schedule()

                # visits() returns client indices into m.clients (0-based among clients only).
                visits = route.visits()

                for k, location_idx in enumerate(visits):
                    # visits() returns location indices; clients start after 2*n_vehicles depots
                    client_model_idx = location_idx - 2 * n_vehicles
                    stop = stops[client_model_idx]
                    planned_stop_ids.add(stop["id"])

                    # schedule[0] is start depot, so client k is at schedule[k+1]
                    scheduled_visit = schedule[k + 1]
                    arrival_time = scheduled_visit.start_service - scheduled_visit.wait_duration

                    vehicle_route.append(
                        {
                            "stop": stop,
                            "type": "stop",
                            "arrival": arrival_time,
                            "duration": arrival_time,
                            "setup": 0,
                            "service": service_durations[client_model_idx],
                            "waiting_time": 0,
                        }
                    )

                # Add end location if vehicle has one.
                route_duration = route.duration()
                if "end_location" in vehicle:
                    vehicle_route.append(
                        {
                            "stop": {
                                "id": f"{vehicle_id}_end",
                                "location": vehicle["end_location"],
                            },
                            "type": "end",
                            "arrival": route_duration,
                            "duration": route_duration,
                            "setup": 0,
                            "service": 0,
                            "waiting_time": 0,
                        }
                    )

                vehicle_routes[vehicle_id] = vehicle_route

            # Determine unplanned stops.
            unplanned = [
                {"id": stop["id"], "location": stop["location"]} for stop in stops if stop["id"] not in planned_stop_ids
            ]

            # Assemble final routes list and statistics.
            for vehicle in vehicles:
                vehicle_id = vehicle["id"]
                vehicle_route = vehicle_routes[vehicle_id]
                stop_count = sum(1 for s in vehicle_route if s["type"] == "stop")
                route_duration = vehicle_route[-1]["duration"] if vehicle_route else 0

                route_entry = {
                    "id": vehicle_id,
                    "route_travel_duration": route_duration,
                    "route": vehicle_route,
                }
                routes.append(route_entry)

                max_route_duration = max(max_route_duration, route_duration)
                activated_vehicles += 1 if stop_count > 0 else 0
                max_stops_in_vehicle = max(max_stops_in_vehicle, stop_count)
                min_stops_in_vehicle = min(min_stops_in_vehicle, stop_count)

            statistics = nextmv.Statistics(
                run=nextmv.RunStatistics(duration=end_time - start_time),
                result=nextmv.ResultStatistics(
                    value=result.cost(),
                    custom={
                        "solution_found": True,
                        "activated_vehicles": activated_vehicles,
                        "max_route_duration": max_route_duration,
                        "max_stops_in_vehicle": max_stops_in_vehicle,
                        "min_stops_in_vehicle": min_stops_in_vehicle,
                    },
                ),
            )

            return nextmv.Output(
                options=input.options,
                solution={"vehicles": routes, "unplanned": unplanned},
                statistics=statistics,
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
                options=input.options,
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
