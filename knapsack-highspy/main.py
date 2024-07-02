"""
Template for working with highspy.
"""

import argparse
import json
import sys
import time
from importlib.metadata import version
from typing import Any

import highspy


def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve problems with highspy.")
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
    h = highspy.Highs()
    h.silent()
    h.setOptionValue("time_limit", duration)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input_data["items"]:
        item_variable = h.addVariable(0.0, 1.0, item["value"])
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    h.addConstr(weights <= input_data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    s = h.maximize(values)

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if h.val(item["variable"]) > 0.9]

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "constraints": h.numConstrs,
                "variables": h.numVariables,
                "status": str(s),
            },
            "value": sum(item["value"] for item in chosen_items),
        },
        "run": {
            "duration": time.time() - start,
            "version": version("highspy"),
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
