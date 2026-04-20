import numbers
import os
import time
from datetime import datetime, timedelta
from importlib.metadata import version
from typing import Any

import nextmv
import numpy as np
import vroom


def main() -> None:
    """Entry point for the program."""

    manifest = nextmv.Manifest.from_yaml(os.path.dirname(os.path.abspath(__file__)))
    options = manifest.extract_options()

    input = nextmv.load(options=options)
    if options.default_duration is not None:
        input.data.setdefault("defaults", {}).setdefault("stops", {})
        input.data["defaults"]["stops"].setdefault("duration", options.default_duration)
    if options.default_lat is not None and options.default_lon is not None:
        depot = {"lat": options.default_lat, "lon": options.default_lon}
        input.data.setdefault("defaults", {}).setdefault("vehicles", {})
        input.data["defaults"]["vehicles"].setdefault("start_location", depot)
        input.data["defaults"]["vehicles"].setdefault("end_location", depot)
    apply_defaults(input.data)
    validate_input(input.data)
    process_duration_matrix(input.data)

    nextmv.log("Solving routing problem:")
    nextmv.log(f"  - vehicles: {len(input.data.get('vehicles', []))}")
    nextmv.log(f"  - stops: {len(input.data.get('stops', []))}")

    model = DecisionModel()
    output = model.solve(input)
    nextmv.write(output)


class DecisionModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        start_time = time.time()
        nextmv.redirect_stdout()  # Solver chatter is logged to stderr.
        input.options.solver = "vroom"
        input.options.version = version("pyvroom")

        # TODO: use duration to limit the runtime of the solver
        _ = input.options.duration

        # Prepare data.
        speed_factors = [v["speed_factor"] if "speed_factor" in v else 1 for v in input.data["vehicles"]]
        capacities = [int(round(v["capacity"])) if "capacity" in v else 0 for v in input.data["vehicles"]]
        quantities = [int(round(s["quantity"])) if "quantity" in s else 0 for s in input.data["stops"]]
        quantities += [0] * (len(input.data["vehicles"]) * 2)
        durations = [int(round(s["duration"])) if "duration" in s else 0 for s in input.data["stops"]]
        durations += [0] * (len(input.data["vehicles"]) * 2)
        max_duration_big_m = 365 * 24 * 60 * 60  # 1 year - used to remove the max_duration constraint if not provided
        max_durations = [
            v["max_duration"] if "max_duration" in v else max_duration_big_m for v in input.data["vehicles"]
        ]
        duration_matrix = input.data["duration_matrix"] if "duration_matrix" in input.data else None

        # Create the routing model.
        problem_instance = vroom.Input()
        problem_instance.set_durations_matrix(
            profile="car",
            matrix_input=duration_matrix,
        )

        # Add the vehicles.
        for i in range(len(input.data["vehicles"])):
            problem_instance.add_vehicle(
                vroom.Vehicle(
                    id=i,
                    start=i * 2 + len(input.data["stops"]),
                    end=i * 2 + 1 + len(input.data["stops"]),
                    profile="car",
                    capacity=[capacities[i]],
                    max_travel_time=max_durations[i],
                    speed_factor=speed_factors[i],
                )
            )

        # Add the stops.
        for i in range(len(input.data["stops"])):
            job = vroom.Job(
                id=i,
                location=i,
                default_service=durations[i],
                delivery=[-quantities[i]],
                pickup=[quantities[i]],
            )
            problem_instance.add_job(job)

        # Solve the problem.
        solution = problem_instance.solve(
            exploration_level=input.options.exploration_level, nb_threads=input.options.threads
        )
        solve_end_time = time.time()

        # Translate the solution into the output format.
        vehicles_by_idx = dict(enumerate(input.data["vehicles"]))
        stops_by_idx = dict(enumerate(input.data["stops"]))
        unplanned_stops = []
        max_travel_duration = 0
        max_duration = 0
        min_travel_duration = None
        min_duration = None
        max_stops_in_vehicle = 0
        min_stops_in_vehicle = len(input.data["stops"])
        activated_vehicles = 0
        routes = []

        if solution:
            # Determine the routes.
            vehicle_routes = {}
            planned_stops = set()

            def convert_stop(
                t: str,
                stop: dict[str, Any],
                row: dict[str, Any],
                prev_cumulative_travel: int,
                base_time: datetime | None,
            ):
                arrival_time = int(row["arrival"])
                waiting_time = int(row["waiting_time"])
                setup = int(row["setup"])
                service = int(row["service"])
                cumulative_travel_duration = int(row["duration"])
                travel_duration = cumulative_travel_duration - prev_cumulative_travel
                start_time = arrival_time + waiting_time
                end_time = start_time + setup + service
                if base_time is not None:
                    fmt_arrival = format_rfc3339(base_time + timedelta(seconds=arrival_time))
                    fmt_start = format_rfc3339(base_time + timedelta(seconds=start_time))
                    fmt_end = format_rfc3339(base_time + timedelta(seconds=end_time))
                else:
                    fmt_arrival = arrival_time
                    fmt_start = start_time
                    fmt_end = end_time
                step = {
                    "stop": stop,
                    "type": t,
                    "travel_duration": travel_duration,
                    "cumulative_travel_duration": cumulative_travel_duration,
                    "arrival_time": fmt_arrival,
                    "start_time": fmt_start,
                    "end_time": fmt_end,
                    "setup": setup,
                    "duration": service,
                    "waiting_time": waiting_time,
                }
                return step, cumulative_travel_duration

            # Iterate dataframe to translate the routes into output format.
            prev_cumulative_travel_by_vehicle: dict[str, int] = {}
            base_time_by_vehicle: dict[str, datetime | None] = {}
            for _, row in solution.routes.iterrows():
                vehicle = vehicles_by_idx[row["vehicle_id"]]
                vid = vehicle["id"]

                if vid not in vehicle_routes:
                    vehicle_routes[vid] = []
                    prev_cumulative_travel_by_vehicle[vid] = 0
                    raw_start = vehicle.get("start_time")
                    base_time_by_vehicle[vid] = parse_rfc3339(raw_start) if raw_start else None

                vehicle_route = vehicle_routes[vid]
                prev_cumulative_travel = prev_cumulative_travel_by_vehicle[vid]
                base_time = base_time_by_vehicle[vid]

                match row["type"]:
                    case "start":
                        if "start_location" in vehicle:
                            step, prev = convert_stop(
                                "start",
                                {
                                    "id": f"{vid}_start",
                                    "location": vehicle["start_location"],
                                },
                                row,
                                prev_cumulative_travel,
                                base_time,
                            )
                            vehicle_route.append(step)
                            prev_cumulative_travel_by_vehicle[vid] = prev
                    case "end":
                        if "end_location" in vehicle:
                            step, prev = convert_stop(
                                "end",
                                {
                                    "id": f"{vid}_end",
                                    "location": vehicle["end_location"],
                                },
                                row,
                                prev_cumulative_travel,
                                base_time,
                            )
                            vehicle_route.append(step)
                            prev_cumulative_travel_by_vehicle[vid] = prev
                    case "job":
                        stop = stops_by_idx[row["location_index"]]
                        planned_stops.add(stop["id"])
                        step, prev = convert_stop("stop", stop, row, prev_cumulative_travel, base_time)
                        vehicle_route.append(step)
                        prev_cumulative_travel_by_vehicle[vid] = prev
                    case _:
                        raise ValueError(f"Unknown route type {row['type']}.")

            # Fully assemble routes.
            for vehicle in input.data["vehicles"]:
                vehicle_route = vehicle_routes.get(vehicle["id"], [])
                route_travel_duration = vehicle_route[-1]["cumulative_travel_duration"] if vehicle_route else 0
                route_stops_duration = sum(
                    step["setup"] + step["duration"] for step in vehicle_route if step["type"] == "stop"
                )
                route_duration = route_travel_duration + route_stops_duration
                route = {
                    "id": vehicle["id"],
                    "route_travel_duration": route_travel_duration,
                    "route_stops_duration": route_stops_duration,
                    "route_duration": route_duration,
                    "route": vehicle_route,
                }
                routes.append(route)
                stop_count = sum(1 for step in vehicle_route if step["type"] == "stop")
                activated_vehicles += 1 if stop_count > 0 else 0
                if stop_count > 0:
                    max_travel_duration = max(max_travel_duration, route_travel_duration)
                    max_duration = max(max_duration, route_duration)
                    min_travel_duration = (
                        route_travel_duration
                        if min_travel_duration is None
                        else min(min_travel_duration, route_travel_duration)
                    )
                    min_duration = route_duration if min_duration is None else min(min_duration, route_duration)
                max_stops_in_vehicle = max(max_stops_in_vehicle, stop_count)
                min_stops_in_vehicle = min(min_stops_in_vehicle, stop_count)

            # Determine the unplanned stops.
            for _, stop in stops_by_idx.items():
                if stop["id"] not in planned_stops:
                    unplanned_stops.append({"id": stop["id"], "location": stop["location"]})

            statistics = nextmv.Statistics(
                run=nextmv.RunStatistics(duration=solve_end_time - start_time),
                result=nextmv.ResultStatistics(
                    duration=solve_end_time - start_time,
                    value=solution.summary.cost,
                    custom={
                        "solution_found": True,
                        "activated_vehicles": activated_vehicles,
                        "max_travel_duration": max_travel_duration,
                        "max_duration": max_duration,
                        "min_travel_duration": min_travel_duration if min_travel_duration is not None else 0,
                        "min_duration": min_duration if min_duration is not None else 0,
                        "max_stops_in_vehicle": max_stops_in_vehicle,
                        "min_stops_in_vehicle": min_stops_in_vehicle,
                    },
                ),
            )

        else:
            statistics = nextmv.Statistics(
                run=nextmv.RunStatistics(duration=solve_end_time - start_time),
                result=nextmv.ResultStatistics(
                    duration=solve_end_time - start_time,
                    value=None,
                ),
            )

        return nextmv.Output(
            options=input.options,
            solution={"vehicles": routes, "unplanned": unplanned_stops},
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
        if "speed_factor" in vehicle and (
            not isinstance(vehicle["speed_factor"], numbers.Number)
            or vehicle["speed_factor"] <= 0
            or vehicle["speed_factor"] > 5
        ):
            raise ValueError(
                f"Invalid speed_factor {vehicle['speed_factor'] if 'speed_factor' in vehicle else None} "
                + f"for vehicle {ident}."
            )
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
    Calculates the distance matrix for the input data. Takes into account whether the
    input data contains vehicle start and end locations.
    """
    # Determine which vehicles have start and end locations.
    has_start = {v["id"]: True for v in input_data["vehicles"] if "start_location" in v}
    has_end = {v["id"]: True for v in input_data["vehicles"] if "end_location" in v}
    # Calculate the distance matrix from the locations using the haversine formula.
    start = time.time()
    lats_origin = np.array([s["location"]["lat"] for s in input_data["stops"]])
    for vehicle in input_data["vehicles"]:
        if vehicle["id"] in has_start:
            lats_origin = np.append(lats_origin, vehicle["start_location"]["lat"])
        if vehicle["id"] in has_end:
            lats_origin = np.append(lats_origin, vehicle["end_location"]["lat"])
    lons_origin = np.array([s["location"]["lon"] for s in input_data["stops"]])
    for vehicle in input_data["vehicles"]:
        if vehicle["id"] in has_start:
            lons_origin = np.append(lons_origin, vehicle["start_location"]["lon"])
        if vehicle["id"] in has_end:
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

    # Reshape to 2D before inserting rows/columns for missing vehicle locations.
    n_init = len(input_data["stops"]) + len(has_start) + len(has_end)
    distances = distances.reshape(n_init, n_init)

    # Insert 0 rows/columns at the correct positions for missing start/end locations.
    # The final layout is: [stops..., v0_start, v0_end, v1_start, v1_end, ...]
    # We track an insertion offset as we insert rows/cols, shifting subsequent indices.
    n_stops = len(input_data["stops"])
    insert_offset = 0
    for i, vehicle in enumerate(input_data["vehicles"]):
        start_idx = n_stops + 2 * i + insert_offset
        if vehicle["id"] not in has_start:
            distances = np.insert(distances, start_idx, 0, axis=0)
            distances = np.insert(distances, start_idx, 0, axis=1)
            insert_offset += 1
        end_idx = n_stops + 2 * i + 1 + insert_offset
        if vehicle["id"] not in has_end:
            distances = np.insert(distances, end_idx, 0, axis=0)
            distances = np.insert(distances, end_idx, 0, axis=1)
            insert_offset += 1

    end = time.time()
    nextmv.log(f"Distance matrix calculation took {round(end - start, 2)} seconds.")
    return distances


def process_duration_matrix(input_data: dict[str, Any]) -> None:
    """Prepares the duration matrix of the input data, if given."""

    # If the input data already contains a duration matrix, return it.
    if "duration_matrix" in input_data:
        np_matrix = np.array(input_data["duration_matrix"])
        input_data["duration_matrix"] = expand_missing_start_end(np_matrix, input_data)
    else:
        # Calculate the distance matrix if no duration matrix is given.
        input_data["duration_matrix"] = calculate_distance_matrix(input_data)

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


def format_rfc3339(value: datetime) -> str:
    """Formats a datetime as an RFC3339 string, using Z instead of +00:00 for UTC."""
    s = value.isoformat()
    if s.endswith("+00:00"):
        s = s[:-6] + "Z"
    return s


def parse_rfc3339(value: str) -> datetime:
    """Parses an RFC3339 string into a datetime, handling Z as UTC offset."""
    if value.endswith("Z"):
        value = value[:-1] + "+00:00"
    return datetime.fromisoformat(value)


if __name__ == "__main__":
    main()
