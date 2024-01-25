"""
Template for working with Pyomo.
"""

import argparse
import json
import logging
import sys
from typing import Any

import pyomo.environ as pyo

# Duration parameter for the solver.
SUPPORTED_PROVIDER_DURATIONS = {
    "cbc": "sec",
    "glpk": "tmlim",
}


# Status of the solver after optimizing.
STATUS = {
    pyo.TerminationCondition.feasible: "suboptimal",
    pyo.TerminationCondition.infeasible: "infeasible",
    pyo.TerminationCondition.optimal: "optimal",
    pyo.TerminationCondition.unbounded: "unbounded",
}


def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve problems with Pyomo.")
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
    parser.add_argument(
        "-provider",
        default="cbc",
        help="Solver provider. Default is cbc.",
    )
    args = parser.parse_args()

    # Read input data, solve the problem and write the solution.
    input_data = read_input(args.input)
    log("Solving knapsack problem:")
    log(f"  - items: {len(input_data.get('items', []))}")
    log(f"  - capacity: {input_data.get('weight_capacity', 0)}")
    log(f"  - max duration: {args.duration} seconds")
    solution = solve(input_data, args.duration, args.provider)
    write_output(args.output, solution)


def solve(input_data: dict[str, Any], duration: int, provider: str) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    # Make sure the provider is supported.
    if provider not in SUPPORTED_PROVIDER_DURATIONS:
        raise ValueError(
            f"Unsupported provider: {provider}. The supported providers are: "
            f"{', '.join(SUPPORTED_PROVIDER_DURATIONS.keys())}"
        )

    # Silence all Pyomo logging.
    logging.getLogger("pyomo.core").setLevel(logging.ERROR)

    # Creates the model.
    model = pyo.ConcreteModel()

    # Creates the solver.
    solver = pyo.SolverFactory(provider)
    solver.options[SUPPORTED_PROVIDER_DURATIONS[provider]] = duration

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables.
    item_ids = [item["id"] for item in input_data["items"]]
    model.item_variable = pyo.Var(item_ids, domain=pyo.Boolean)

    # Use the decision variables for the linear sums
    items = []
    for item in input_data["items"]:
        item_id = item["id"]
        items.append({"item": item, "variable": model.item_variable[item_id]})
        weights += model.item_variable[item_id] * item["weight"]
        values += model.item_variable[item_id] * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.constraint = pyo.Constraint(expr=weights <= input_data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.objective = pyo.Objective(expr=values, sense=pyo.maximize)

    # Solves the problem.
    results = solver.solve(model)

    # Convert to solution format.
    value = pyo.value(model.objective, exception=False)
    chosen_items = []
    if value:
        chosen_items = [item["item"] for item in items if item["variable"]() > 0.9]

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "constraints": model.nconstraints(),
                "provider": provider,
                "status": STATUS.get(results.solver.termination_condition, "unknown"),
                "variables": model.nvariables(),
            },
            "duration": results.solver.time,
            "value": value,
        },
        "run": {
            "duration": results.solver.time,
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
