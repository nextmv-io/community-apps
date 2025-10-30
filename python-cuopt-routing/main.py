#!/usr/bin/env python3


from datetime import datetime

import cudf
import nextmv
from cuopt import routing
from haversine import Unit, haversine
from visual import create_visual

SOLUTION_STATUS = {s.value: s.name for s in routing.SolutionStatus}


def create_distance_matrix(locations):
    nextmv.log(f"Creating {len(locations)}^2 distance matrix")
    """Create a distance matrix from a list of [lon, lat] coordinates."""
    matrix = []
    for source in locations:
        # haversine expects (lat, lon) tuples
        row = [
            haversine(
                reversed(source),
                reversed(dest),
                unit=Unit.KILOMETERS,
            )
            for dest in locations
        ]
        matrix.append(row)
    return matrix


def main() -> None:
    start = datetime.now()

    options = nextmv.Options(nextmv.Option("time_limit", float, default=1))

    data = nextmv.load().data

    # Build all locations: vehicle starts + vehicle ends + stops
    all_locations = []  # (lon, lat) coordinates
    vehicle_starts = []  # location indices
    vehicle_ends = []  # location indices

    # Add vehicle start locations
    for vehicle in data["vehicles"]:
        all_locations.append(vehicle["start"])
        vehicle_starts.append(len(all_locations) - 1)

    # Add job locations
    for job in data["jobs"]:
        all_locations.append(job["location"])

    # Add vehicle end locations
    for vehicle in data["vehicles"]:
        all_locations.append(vehicle["end"])
        vehicle_ends.append(len(all_locations) - 1)

    # Create distance matrix
    distance_matrix = cudf.DataFrame(
        create_distance_matrix(all_locations),
        dtype="float32",
    )

    # Create routing data model
    data_model = routing.DataModel(
        distance_matrix.shape[0],
        len(data["vehicles"]),
        len(data["jobs"]),
    )
    data_model.add_cost_matrix(distance_matrix)

    # Set vehicle origins and destinations
    data_model.set_vehicle_locations(
        cudf.Series(vehicle_starts, dtype="int32"),
        cudf.Series(vehicle_ends, dtype="int32"),
    )

    # Add capacity constraints
    job_demands = [job["delivery"][0] for job in data["jobs"]]
    vehicle_capacities = [v["capacity"][0] for v in data["vehicles"]]

    data_model.add_capacity_dimension(
        "demand",
        cudf.Series(job_demands, dtype="int32"),
        cudf.Series(vehicle_capacities, dtype="int32"),
    )

    solver_settings = routing.SolverSettings()
    solver_settings.set_time_limit(options.time_limit)

    nextmv.log("Solving model with cuOpt")
    solution = routing.Solve(data_model, solver_settings)

    # Convert solution to dict for output and visualization
    solution_dict = solution.route.to_dict(orient="records")

    nextmv.write(
        nextmv.Output(
            options=options,
            solution=solution_dict,
            statistics=nextmv.Statistics(
                run=nextmv.RunStatistics(
                    duration=(datetime.now() - start).total_seconds(),
                ),
                result=nextmv.ResultStatistics(
                    value=solution.get_total_objective(),
                    custom={
                        "status": SOLUTION_STATUS[solution.get_status()],
                        "vehicle_count": solution.get_vehicle_count(),
                    },
                ),
            ),
            assets=[create_visual(data, solution_dict)],
        ),
    )


if __name__ == "__main__":
    main()
