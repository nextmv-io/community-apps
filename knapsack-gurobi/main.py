"""
Template for working with Gurobi.
"""

import argparse
import json
import os
import sys
import time
from typing import Any

import gurobipy as gp
from gurobipy import GRB

# Status of the solver after optimizing.
STATUS = {
    GRB.SUBOPTIMAL: "suboptimal",
    GRB.INFEASIBLE: "infeasible",
    GRB.OPTIMAL: "optimal",
    GRB.UNBOUNDED: "unbounded",
}


def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve problems with Gurobi.")
    parser.add_argument(
        "-input",
        default="",
        help="Path to input file. Default is stdin.",
    )
    parser.add_argument(
        "-output",
        default="",
        help="Path to output file. Default is stdout.",
    )
    parser.add_argument(
        "-duration",
        default=30,
        help="Max runtime duration (in seconds). Default is 30.",
        type=int,
    )
    args = parser.parse_args()

    # Read input data, solve the problem and write the solution.
    input_data = read_input(args.input)
    log("Solving knapsack problem:")
    log(f"  - items: {len(input_data.get('items', []))}")
    log(f"  - capacity: {input_data.get('weight_capacity', 0)}")
    log(f"  - max duration: {args.duration} seconds")
    solution = solve(input_data, args.duration)
    write_output(args.output, solution)


def solve(input_data: dict[str, Any], duration: int) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    start_time = time.time()

    # Creates the environment.
    env = gp.Env(empty=True)
    env.setParam("OutputFlag", 0)

    # Read the license file, if available.
    if os.path.isfile("gurobi.lic"):
        env.readParams("gurobi.lic")

    # Creates the model.
    env.start()
    model = gp.Model(env=env)
    model.Params.TimeLimit = duration

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input_data["items"]:
        item_variable = model.addVar(vtype=GRB.BINARY, name=item["id"])
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.addConstr(weights <= input_data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.setObjective(expr=values, sense=GRB.MAXIMIZE)

    # Solves the problem.
    model.optimize()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if item["variable"].X > 0.9]

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "constraints": model.NumConstrs,
                "provider": "gurobi",
                "status": STATUS.get(model.Status, "unknown"),
                "variables": model.NumVars,
            },
            "duration": model.Runtime,
            "value": model.ObjVal,
        },
        "run": {
            "duration": time.time() - start_time,
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


def read_input(input_path) -> dict[str, Any]:
    """Reads the input from stdin or a given input file."""

    input_file = {}
    if input_path:
        with open(input_path, encoding="utf-8") as file:
            input_file = json.load(file)
    else:
        input_file = json.load(sys.stdin)

    return input_file


def write_output(output_path, output) -> None:
    """Writes the output to stdout or a given output file."""

    content = json.dumps(output, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
