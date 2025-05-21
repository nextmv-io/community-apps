import math
import time

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


class DecisionModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        # Redirect solver chatter to stderr.
        nextmv.redirect_stdout()

        # Solve the problem.
        solution, statistics = solve(input.data, input.options.provider, input.options.duration)

        # Prepare the output.
        return nextmv.Output(
            options=input.options,
            solution=solution,
            statistics=nextmv.Statistics.from_dict(statistics),
        )


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Option("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Option("provider", str, "SCIP", "Solver provider.", False),
    )

    input = nextmv.load(options=options, path=options.input)

    nextmv.log("Solving region allocation:")
    nextmv.log(f"  - regions: {len(input.data.get('regions', []))}")
    nextmv.log(f"  - hubs: {len(input.data.get('hubs', []))}")
    nextmv.log(f"  - duration: {options.duration} seconds")
    nextmv.log(f"  - provider: {options.provider}")

    model = DecisionModel()
    output = model.solve(input)
    nextmv.write(output, path=options.output)


if __name__ == "__main__":
    main()
