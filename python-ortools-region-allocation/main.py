import math
import time
from typing import Any

import nextmv
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


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving region allocation:")
    nextmv.log(f"  - regions: {len(loaded_input.data.get('regions', []))}")
    nextmv.log(f"  - hubs: {len(loaded_input.data.get('hubs', []))}")
    nextmv.log(f"  - duration: {options.duration} seconds")
    nextmv.log(f"  - provider: {options.provider}")

    solution, metrics = solve(loaded_input, options)
    nextmv.write(solution=solution, metrics=metrics, options=options)


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


def solve(loaded_input: nextmv.Input, options: nextmv.Options) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    # Redirect solver chatter to stderr.
    nextmv.redirect_stdout()

    # Creates the solver.
    start_time = time.time()
    solver = pywraplp.Solver.CreateSolver(options.provider)
    solver.SetTimeLimit(options.duration * 1000)

    # Prepare the distance matrix.
    distance_matrix = {}
    for region in loaded_input.data["regions"]:
        for hub in loaded_input.data["hubs"]:
            distance = calculate_distance(region, hub)
            distance_matrix[(region["id"], hub["id"])] = distance

    # Creates the decision variables.
    assignments = {}
    for region in loaded_input.data["regions"]:
        for hub in loaded_input.data["hubs"]:
            variable = solver.IntVar(0, 1, f"{region['id']}_{hub['id']}")
            assignments[(region["id"], hub["id"])] = variable

    # Make sure that each region is assigned to exactly one hub.
    for region in loaded_input.data["regions"]:
        solver.Add(sum(assignments[(region["id"], hub["id"])] for hub in loaded_input.data["hubs"]) == 1)

    # Make sure that the demand of the regions assigned to the hub is covered by its capacity.
    for hub in loaded_input.data["hubs"]:
        solver.Add(
            sum(assignments[(region["id"], hub["id"])] * region["demand"] for region in loaded_input.data["regions"])
            <= hub["capacity"]
        )

    # Set the objective function to minimize the total distance.
    objective = solver.Objective()
    for region in loaded_input.data["regions"]:
        for hub in loaded_input.data["hubs"]:
            distance = distance_matrix[(region["id"], hub["id"])]
            objective.SetCoefficient(assignments[(region["id"], hub["id"])], distance)
    objective.SetMinimization()

    # Solves the problem.
    status = solver.Solve()

    # Get the assigned regions.
    assignments_result = {
        region["id"]: next(
            hub["id"]
            for hub in loaded_input.data["hubs"]
            if assignments[(region["id"], hub["id"])].solution_value() > 0.5
        )
        for region in loaded_input.data["regions"]
    }
    solution = {
        "assignments": assignments_result,
        "hubs": loaded_input.data["hubs"],
        "regions": loaded_input.data["regions"],
    }

    # Collect metrics.
    metrics = {
        "run_duration": time.time() - start_time,
        "solver_duration": solver.WallTime() / 1000,
        "objective_value": solver.Objective().Value(),
        "status": STATUS.get(status, "unknown"),
        "variables": solver.NumVariables(),
        "constraints": solver.NumConstraints(),
    }

    return solution, metrics


if __name__ == "__main__":
    main()
