import argparse
import json
import math
import os
import time

import nextmv
import nextmv.cloud
from ortools.linear_solver import pywraplp

# Status of the solver after optimizing.
STATUS = {
    pywraplp.Solver.FEASIBLE: "suboptimal",
    pywraplp.Solver.INFEASIBLE: "infeasible",
    pywraplp.Solver.OPTIMAL: "optimal",
    pywraplp.Solver.UNBOUNDED: "unbounded",
    pywraplp.Solver.ABNORMAL: "abnormal",
    pywraplp.Solver.NOT_SOLVED: "not_solved",
    pywraplp.Solver.MODEL_INVALID: "model_invalid",
}


def solve(
    input: dict,
    provider: str,
    duration: int,
) -> tuple[dict, str]:
    """Solves the region allocation problem and returns the solution."""
    # Creates the solver.
    start_time = time.time()
    solver = pywraplp.Solver.CreateSolver(provider)
    solver.SetTimeLimit(duration * 1000)

    # Prepare the distance matrix.
    distance_matrix = {}
    for region in input["regions"]:
        for hub in input["hubs"]:
            distance = calculate_distance(region, hub)
            distance_matrix[(region["id"], hub["id"])] = distance

    # Creates the decision variables.
    assignments = {}
    for region in input["regions"]:
        for hub in input["hubs"]:
            variable = solver.IntVar(0, 1, f"{region['id']}_{hub['id']}")
            assignments[(region["id"], hub["id"])] = variable

    # Make sure that each region is assigned to exactly one hub.
    for region in input["regions"]:
        solver.Add(sum(assignments[(region["id"], hub["id"])] for hub in input["hubs"]) == 1)

    # Make sure that the demand of the regions assigned to the hub is covered by its capacity.
    for hub in input["hubs"]:
        solver.Add(
            sum(assignments[(region["id"], hub["id"])] * region["demand"] for region in input["regions"])
            <= hub["capacity"]
        )

    # Set the objective function to minimize the total distance.
    objective = solver.Objective()
    for region in input["regions"]:
        for hub in input["hubs"]:
            distance = distance_matrix[(region["id"], hub["id"])]
            objective.SetCoefficient(assignments[(region["id"], hub["id"])], distance)
    objective.SetMinimization()

    # Solves the problem.
    status = solver.Solve()

    # Get the assigned regions.
    assignments_result = {
        region["id"]: next(
            hub["id"] for hub in input["hubs"] if assignments[(region["id"], hub["id"])].solution_value() > 0.5
        )
        for region in input["regions"]
    }
    solution = {
        "assignments": assignments_result,
        "hubs": input["hubs"],
        "regions": input["regions"],
    }

    # Collect some statistics.
    statistics = {
        "run": {
            "duration": time.time() - start_time,
        },
        "result": {
            "duration": solver.WallTime() / 1000,
            "value": solver.Objective().Value(),
            "custom": {
                "status": STATUS.get(status, "unknown"),
                "variables": solver.NumVariables(),
                "constraints": solver.NumConstraints(),
            },
        },
    }

    return solution, statistics


def calculate_distance(region: dict, hub: dict) -> float:
    """Calculates the distance between a region and a hub using the haversine formula."""
    region_coords = region["center"]
    hub_coords = hub["center"]
    lat1, lon1 = region_coords["y"], region_coords["x"]
    lat2, lon2 = hub_coords["y"], hub_coords["x"]

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])

    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of Earth in kilometers. Use 3956 for miles
    r = 6371

    # Calculate the result
    return c * r


if __name__ == "__main__":
    # Parse the command line arguments.
    parser = argparse.ArgumentParser(description="Region allocation problem solver.")
    parser.add_argument("-input", type=str, help="Path to the input JSON file.")
    parser.add_argument("-output", type=str, help="Path to the input JSON file.")
    parser.add_argument("-provider", type=str, default="SCIP", help="Solver provider.")
    parser.add_argument("-duration", type=int, default=60, help="Max duration in seconds.")
    args = parser.parse_args()

    # Read the input data.
    with open(args.input) as f:
        input_data = json.load(f)

    # Solve the problem.
    before = time.time()
    output_data, statistics = solve(
        input=input_data,
        provider="SCIP",
        duration=60,
    )

    # Write the output data.
    with open(args.output, "w") as f:
        json.dump(output_data, f, indent=2)

    # >>> POST TRACKED RUN TO NEXTMV PLATFORM
    # Note: Above code is intentionally not using nextmv features to better demonstrate
    #       that tracking a run can be added easily to any existing code. You only need
    #       lines below.
    client = nextmv.cloud.Client(api_key=os.environ.get("NEXTMV_API_KEY_PROD"))
    app = nextmv.cloud.Application(client=client, id="demo-app-7")
    tracked_result = app.track_run_with_result(
        tracked_run=nextmv.cloud.TrackedRun(
            input=input_data,
            output=output_data,
            duration=nextmv.cloud.run_duration(
                start=before,
                end=time.time(),
            ),
            status=nextmv.cloud.StatusV2.succeeded,
            error=None,
            logs="Hello world",
        ),
    )
    nextmv.log(f"Tracked run: {tracked_result.id}")
    nextmv.log(f"Tracked run URL: {tracked_result.console_url}")
