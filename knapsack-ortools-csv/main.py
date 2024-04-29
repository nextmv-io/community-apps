"""
Template for working with Google OR-Tools.
"""

import argparse
import csv
import json
import os
import sys
import time
from typing import Any

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
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve problems with OR-Tools.")
    parser.add_argument(
        "-duration",
        default=30,
        help="Max runtime duration (in seconds). Default is 30.",
        type=int,
    )
    args = parser.parse_args()

    # Read input data, solve the problem and write the solution.
    input_data = read_input()

    log("Solving knapsack problem:")
    log(f"  - items: {len(input_data.get('items', []))}")
    log(f"  - capacity: {input_data.get('weight_capacity', 0)}")
    log(f"  - max duration: {args.duration} seconds")

    solution = solve(input_data, args.duration)
    write_output(solution)


def solve(input_data: dict[str, Any], duration: int) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    start = time.time()

    # Creates the solver.
    provider = "SCIP"
    solver = pywraplp.Solver.CreateSolver(provider)
    solver.SetTimeLimit(duration * 1000)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input_data["items"]:
        item_variable = solver.IntVar(0, 1, item["id"])
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    solver.Add(weights <= input_data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    solver.Maximize(values)

    # Solves the problem.
    status = solver.Solve()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if item["variable"].solution_value() > 0.9]

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "constraints": solver.NumConstraints(),
                "provider": provider,
                "status": STATUS.get(status, "unknown"),
                "variables": solver.NumVariables(),
            },
            "duration": solver.WallTime() / 1000,
            "value": solver.Objective().Value(),
        },
        "run": {
            "duration": time.time() - start,
        },
        "schema": "v1",
    }

    return {
        "solutions": [{"items": chosen_items}],
        "statistics": statistics,
    }


def log(message: str) -> None:
    """Logs a message. We need to use stderr since stdout is used for the
    solution."""

    print(message, file=sys.stderr)


def read_input() -> dict[str, Any]:
    """Reads the inputs from the .input dir and transforms into a single object."""

    input_dir = "input"

    with open(f"{input_dir}/items.csv") as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
        items = list(reader)

    with open(f"{input_dir}/weight_capacity.csv") as f:
        reader = csv.DictReader(f, quoting=csv.QUOTE_NONNUMERIC)
        weight_capacity = list(reader)[0]["weight_capacity"]

    input_data = {
        "items": items,
        "weight_capacity": weight_capacity,
    }

    return input_data


def write_output(output: dict[str, Any]) -> None:
    """Writes the output the .output folder and prints the statistics to stdout."""

    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    solution = output["solutions"][0]["items"]
    with open(f"{output_dir}/solution.csv", "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=solution[0].keys(),
            quoting=csv.QUOTE_NONNUMERIC,
        )
        writer.writeheader()
        writer.writerows(solution)

    statistics = output["statistics"]
    print(json.dumps(statistics, indent=2))


if __name__ == "__main__":
    main()
