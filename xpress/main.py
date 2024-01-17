"""
Template for working with FICO Xpress.
"""

import argparse
import json
import sys
from typing import Any

try:
    import xpress as xp
except ImportError as exc:
    raise ImportError("is xpress available for your OS and ARCH and installed?") from exc


# Status of the solver after optimizing.
STATUS = {
    xp.SolStatus.FEASIBLE: "suboptimal",
    xp.SolStatus.INFEASIBLE: "infeasible",
    xp.SolStatus.OPTIMAL: "optimal",
    xp.SolStatus.UNBOUNDED: "unbounded",
}


def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve problems with Xpress.")
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

    # Creates the problem.
    xp.controls.outputlog = 0  # Turns off verbosity.
    problem = xp.problem()
    problem.setControl("timelimit", duration)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input_data["items"]:
        item_variable = xp.var(vartype=xp.binary, name=item["id"])
        problem.addVariable(item_variable)
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    problem.addConstraint(weights <= input_data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    problem.setObjective(values, sense=xp.maximize)

    # Solves the problem.
    _, status = problem.optimize()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if problem.getSolution(item["variable"]) > 0.9]

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "constraints": problem.getAttrib("rows"),
                "provider": "xpress",
                "status": STATUS.get(status, "unknown"),
                "variables": problem.getAttrib("cols"),
            },
            "duration": problem.getAttrib("time"),
            "value": problem.getAttrib("objval"),
        },
        "run": {
            "duration": problem.getAttrib("time"),
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
