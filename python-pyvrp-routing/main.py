import numbers
import os
import time
from datetime import datetime, timedelta
from importlib.metadata import version
from typing import Any

import nextmv
import numpy as np
from pyvrp import IteratedLocalSearchParams, Model, PenaltyParams, SolveParams
from pyvrp.search import NeighbourhoodParams, PerturbationParams
from pyvrp.stop import MaxRuntime


def main() -> None:
    """Entry point for the program."""

    manifest = nextmv.Manifest.from_yaml(os.path.dirname(os.path.abspath(__file__)))
    options = manifest.extract_options()

    # Read and prepare the input data.
    loaded_input = nextmv.load(options=options, path=options.input)
    apply_defaults(loaded_input.data)
    validate_input(loaded_input.data)
    process_distance_matrix(loaded_input.data)
    process_duration_matrix(loaded_input.data)

    nextmv.log("Solving routing problem:")
    nextmv.log(f"  - vehicles: {len(loaded_input.data.get('vehicles', []))}")
    nextmv.log(f"  - stops: {len(loaded_input.data.get('stops', []))}")

    output = solve(loaded_input, options.duration, options)
    nextmv.write(output, path=options.output, options=loaded_input.options)


def make_stop_time(base_dt: datetime | None, seconds: int) -> str | None:
    """Returns an ISO8601 timestamp string for base_dt + seconds, or None if base_dt is None."""
    if base_dt is None:
        return None
    return (base_dt + timedelta(seconds=int(seconds))).isoformat()


def solve(input: nextmv.Input, duration: int, options: Any) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.
    input.options.solver = "PyVRP"
    input.options.version = version("pyvrp")

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
                    dur = int(round(dist / speed))
                    m.add_edge(
                        all_locations[from_pyvrp_idx],
                        all_locations[to_pyvrp_idx],
                        distance=dist,
                        duration=dur,
                        profile=profiles[i],
                    )

    # Whether an explicit distance matrix was provided (for travel_distance output fields).
    has_distance_matrix = "distance_matrix" in input.data
    actual_distance_matrix = input.data.get("distance_matrix") if has_distance_matrix else None

    # Solve the problem.
    start_time = time.time()
    result = m.solve(
        stop=MaxRuntime(duration),
        display=False,
        params=solve_params_from_options(options),
    )
    end_time = time.time()

    routes = []
    if result.is_feasible():
        best = result.best

        # Build a map from vehicle type index to vehicle data.
        max_route_duration = 0
        max_duration = 0
        min_route_duration = None
        min_duration = None
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
            vehicle_route, route_planned_ids = build_vehicle_route(
                route=route,
                vehicle=vehicle,
                stops=stops,
                n_vehicles=n_vehicles,
                service_durations=service_durations,
                pyvrp_to_matrix_idx=pyvrp_to_matrix_idx,
                has_distance_matrix=has_distance_matrix,
                actual_distance_matrix=actual_distance_matrix,
            )
            planned_stop_ids.update(route_planned_ids)
            vehicle_routes[vehicle["id"]] = vehicle_route

        # Determine unplanned stops.
        unplanned = [
            {"id": stop["id"], "location": stop["location"]} for stop in stops if stop["id"] not in planned_stop_ids
        ]

        # Assemble final routes list and statistics.
        for vehicle in vehicles:
            vehicle_id = vehicle["id"]
            vehicle_route = vehicle_routes[vehicle_id]
            stop_count = sum(1 for s in vehicle_route if "duration" in s)
            route_travel_duration = vehicle_route[-1]["cumulative_travel_duration"] if vehicle_route else 0
            route_stops_duration = sum(s.get("duration", 0) for s in vehicle_route)
            route_duration = route_travel_duration + route_stops_duration

            route_entry: dict[str, Any] = {
                "id": vehicle_id,
                "route_travel_duration": route_travel_duration,
                "route_stops_duration": route_stops_duration,
                "route_duration": route_duration,
            }
            if has_distance_matrix and vehicle_route:
                route_entry["route_travel_distance"] = vehicle_route[-1].get("cumulative_travel_distance", 0)
            route_entry["route"] = vehicle_route
            routes.append(route_entry)

            activated_vehicles += 1 if stop_count > 0 else 0
            if stop_count > 0:
                max_route_duration = max(max_route_duration, route_travel_duration)
                max_duration = max(max_duration, route_duration)
                min_route_duration = (
                    route_travel_duration
                    if min_route_duration is None
                    else min(min_route_duration, route_travel_duration)
                )
                min_duration = route_duration if min_duration is None else min(min_duration, route_duration)
            max_stops_in_vehicle = max(max_stops_in_vehicle, stop_count)
            min_stops_in_vehicle = min(min_stops_in_vehicle, stop_count)

        return nextmv.Output(
            options=input.options,
            solution={"vehicles": routes, "unplanned": unplanned},
            metrics={
                "duration": end_time - start_time,
                "value": result.cost(),
                "solution_found": True,
                "activated_vehicles": activated_vehicles,
                "max_travel_duration": max_route_duration,
                "max_duration": max_duration,
                "min_travel_duration": min_route_duration if min_route_duration is not None else 0,
                "min_duration": min_duration if min_duration is not None else 0,
                "max_stops_in_vehicle": max_stops_in_vehicle,
                "min_stops_in_vehicle": min_stops_in_vehicle,
            },
        )
    else:
        return nextmv.Output(
            options=input.options,
            solution={"vehicles": routes, "unplanned": []},
            metrics={
                "duration": end_time - start_time,
                "value": None,
                "solution_found": False,
            },
        )


def build_vehicle_route(
    route: Any,
    vehicle: dict[str, Any],
    stops: list[dict[str, Any]],
    n_vehicles: int,
    service_durations: list[int],
    pyvrp_to_matrix_idx: Any,
    has_distance_matrix: bool,
    actual_distance_matrix: Any,
) -> tuple[list[dict[str, Any]], set[str]]:
    """Builds the route entry list and the set of planned stop IDs for one vehicle route."""

    vehicle_id = vehicle["id"]
    vehicle_route: list[dict[str, Any]] = []
    planned_stop_ids: set[str] = set()

    # Parse ISO8601 vehicle start_time reference if present (for absolute timestamps).
    base_dt: datetime | None = None
    if "start_time" in vehicle:
        base_dt = datetime.fromisoformat(vehicle["start_time"])

    # Get scheduled visits for the route.
    # schedule() includes depot visits: [start_depot, client_0, ..., client_n, end_depot]
    schedule = route.schedule()
    # visits() only includes client visits: [client_0, ..., client_n]
    visits = route.visits()

    # Build the ordered sequence of PyVRP location indices for this route.
    vt_idx = route.vehicle_type()
    start_depot_pyvrp_idx = 2 * vt_idx
    end_depot_pyvrp_idx = 2 * vt_idx + 1
    pyvrp_location_sequence = [start_depot_pyvrp_idx] + list(visits) + [end_depot_pyvrp_idx]

    cumulative_travel_duration = 0
    cumulative_travel_distance = 0

    # Add start location if vehicle has one.
    if "start_location" in vehicle:
        start_entry: dict[str, Any] = {
            "stop": {
                "id": f"{vehicle_id}-start",
                "location": vehicle["start_location"],
            },
            "travel_duration": 0,
            "cumulative_travel_duration": 0,
        }
        if has_distance_matrix:
            start_entry["travel_distance"] = 0
            start_entry["cumulative_travel_distance"] = 0
        if base_dt is not None:
            start_depot_time = make_stop_time(base_dt, schedule[0].start_service)
            start_entry["arrival_time"] = start_depot_time
            start_entry["start_time"] = start_depot_time
            start_entry["end_time"] = start_depot_time
        vehicle_route.append(start_entry)

    for k, location_idx in enumerate(visits):
        # visits() returns location indices; clients start after 2*n_vehicles depots
        client_model_idx = location_idx - 2 * n_vehicles
        stop = stops[client_model_idx]
        planned_stop_ids.add(stop["id"])

        # schedule[0] is start depot, so client k is at schedule[k+1]
        sv = schedule[k + 1]
        prev_sv = schedule[k]

        # Compute per-leg travel duration.
        prev_end_service = prev_sv.start_service + (0 if k == 0 else service_durations[visits[k - 1] - 2 * n_vehicles])
        arrival_seconds = sv.start_service - sv.wait_duration
        leg_travel_duration = arrival_seconds - prev_end_service
        cumulative_travel_duration += leg_travel_duration

        # Compute per-leg travel distance if distance matrix is available.
        leg_travel_distance = 0
        if has_distance_matrix:
            from_mat = pyvrp_to_matrix_idx(pyvrp_location_sequence[k])
            to_mat = pyvrp_to_matrix_idx(pyvrp_location_sequence[k + 1])
            leg_travel_distance = int(actual_distance_matrix[from_mat][to_mat])
            cumulative_travel_distance += leg_travel_distance

        service_dur = service_durations[client_model_idx]
        start_service_seconds = sv.start_service
        end_service_seconds = start_service_seconds + service_dur

        client_entry: dict[str, Any] = {
            "stop": {
                "id": stop["id"],
                "location": stop["location"],
            },
            "travel_duration": leg_travel_duration,
            "cumulative_travel_duration": cumulative_travel_duration,
        }
        if has_distance_matrix:
            client_entry["travel_distance"] = leg_travel_distance
            client_entry["cumulative_travel_distance"] = cumulative_travel_distance
        if base_dt is not None:
            client_entry["arrival_time"] = make_stop_time(base_dt, arrival_seconds)
            client_entry["start_time"] = make_stop_time(base_dt, start_service_seconds)
            client_entry["end_time"] = make_stop_time(base_dt, end_service_seconds)
        client_entry["duration"] = service_dur
        if sv.wait_duration > 0:
            client_entry["waiting_time"] = sv.wait_duration
        vehicle_route.append(client_entry)

    # Add end location if vehicle has one.
    if "end_location" in vehicle:
        end_sv = schedule[-1]
        last_client_sv = schedule[-2]
        last_client_model_idx = visits[-1] - 2 * n_vehicles if visits else None
        last_client_service = service_durations[last_client_model_idx] if last_client_model_idx is not None else 0

        prev_end_service_for_end = last_client_sv.start_service + last_client_service
        end_arrival_seconds = end_sv.start_service - end_sv.wait_duration
        end_leg_travel_duration = end_arrival_seconds - prev_end_service_for_end
        cumulative_travel_duration += end_leg_travel_duration

        end_leg_travel_distance = 0
        if has_distance_matrix:
            from_mat = pyvrp_to_matrix_idx(pyvrp_location_sequence[-2])
            to_mat = pyvrp_to_matrix_idx(pyvrp_location_sequence[-1])
            end_leg_travel_distance = int(actual_distance_matrix[from_mat][to_mat])
            cumulative_travel_distance += end_leg_travel_distance

        end_entry: dict[str, Any] = {
            "stop": {
                "id": f"{vehicle_id}-end",
                "location": vehicle["end_location"],
            },
            "travel_duration": end_leg_travel_duration,
            "cumulative_travel_duration": cumulative_travel_duration,
        }
        if has_distance_matrix:
            end_entry["travel_distance"] = end_leg_travel_distance
            end_entry["cumulative_travel_distance"] = cumulative_travel_distance
        if base_dt is not None:
            end_time_str = make_stop_time(base_dt, end_arrival_seconds)
            end_entry["arrival_time"] = end_time_str
            end_entry["start_time"] = end_time_str
            end_entry["end_time"] = end_time_str
        vehicle_route.append(end_entry)

    return vehicle_route, planned_stop_ids


def solve_params_from_options(options: Any) -> SolveParams:
    """Builds a SolveParams from manifest options, skipping any that are unset (None).

    Only options explicitly provided by the caller are forwarded to each
    parameter dataclass; unset options fall back to PyVRP's own defaults.
    """

    def _get(name: str) -> Any:
        return getattr(options, name, None)

    ils_kwargs: dict[str, Any] = {}
    if (v := _get("num_iters_no_improvement")) is not None:
        ils_kwargs["num_iters_no_improvement"] = v
    if (v := _get("history_length")) is not None:
        ils_kwargs["history_length"] = v
    if (v := _get("exhaustive_on_best")) is not None:
        ils_kwargs["exhaustive_on_best"] = v

    penalty_kwargs: dict[str, Any] = {}
    if (v := _get("solutions_between_updates")) is not None:
        penalty_kwargs["solutions_between_updates"] = v
    if (v := _get("penalty_increase")) is not None:
        penalty_kwargs["penalty_increase"] = v
    if (v := _get("penalty_decrease")) is not None:
        penalty_kwargs["penalty_decrease"] = v
    if (v := _get("target_feasible")) is not None:
        penalty_kwargs["target_feasible"] = v
    if (v := _get("feas_tolerance")) is not None:
        penalty_kwargs["feas_tolerance"] = v
    if (v := _get("min_penalty")) is not None:
        penalty_kwargs["min_penalty"] = v
    if (v := _get("max_penalty")) is not None:
        penalty_kwargs["max_penalty"] = v

    neighbourhood_kwargs: dict[str, Any] = {}
    if (v := _get("weight_wait_time")) is not None:
        neighbourhood_kwargs["weight_wait_time"] = v
    if (v := _get("weight_time_warp")) is not None:
        neighbourhood_kwargs["weight_time_warp"] = v
    if (v := _get("num_neighbours")) is not None:
        neighbourhood_kwargs["num_neighbours"] = v
    if (v := _get("symmetric_proximity")) is not None:
        neighbourhood_kwargs["symmetric_proximity"] = v
    if (v := _get("symmetric_neighbours")) is not None:
        neighbourhood_kwargs["symmetric_neighbours"] = v

    perturbation_kwargs: dict[str, Any] = {}
    if (v := _get("min_perturbations")) is not None:
        perturbation_kwargs["min_perturbations"] = v
    if (v := _get("max_perturbations")) is not None:
        perturbation_kwargs["max_perturbations"] = v

    return SolveParams(
        ils=IteratedLocalSearchParams(**ils_kwargs),
        penalty=PenaltyParams(**penalty_kwargs),
        neighbourhood=NeighbourhoodParams(**neighbourhood_kwargs),
        perturbation=PerturbationParams(**perturbation_kwargs),
    )


def apply_defaults(input_data: dict[str, Any]) -> None:
    """
    Applies default values to the vehicles and stops
    (if they are given and not already set on them directly).
    """
    if "defaults" not in input_data:
        return
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
