"""
Template for working with the pyoptinterface library.
"""

import argparse
import json
import sys
import time
from importlib.metadata import version
from typing import Any

import pyoptinterface as poi
from pyoptinterface import highs


def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve problems with the pyoptinterface library.")
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

    start = time.time()

    # Creates the solver.
    model = highs.Model()
    model.set_model_attribute(poi.ModelAttribute.TimeLimitSec, duration)
    model.set_model_attribute(poi.ModelAttribute.Silent, True)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input_data["items"]:
        item_variable = model.add_variable(
            lb=0.0,
            ub=1.0,
            domain=poi.VariableDomain.Integer,
            name=item["id"],
        )
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.add_linear_constraint(
        expr=weights,
        sense=poi.ConstraintSense.LessEqual,
        rhs=input_data["weight_capacity"],
        name="weight_capacity",
    )

    # Sets the objective function: maximize the value of the chosen items.
    status = model.set_objective(
        expr=values,
        sense=poi.ObjectiveSense.Maximize,
    )

    # Solves the problem.
    model.optimize()
    status = model.get_model_attribute(poi.ModelAttribute.TerminationStatus)

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if model.get_value(item["variable"]) > 0.9]

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "constraints": model.number_of_constraints(type=poi.ConstraintType.Linear),
                "variables": model.number_of_variables(),
                "status": str(status),
            },
            "value": sum(item["value"] for item in chosen_items),
        },
        "run": {
            "duration": time.time() - start,
            "version": version("pyoptinterface"),
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


def read_input(input_path: str) -> dict[str, Any]:
    """Reads the input from stdin or a given input file."""

    input_file = {}
    if input_path:
        with open(input_path, encoding="utf-8") as file:
            input_file = json.load(file)
    else:
        input_file = json.load(sys.stdin)

    return input_file


def write_output(output_path: str, output: dict[str, Any]) -> None:
    """Writes the output to stdout or a given output file."""

    content = json.dumps(output, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
