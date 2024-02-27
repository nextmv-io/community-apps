"""
Template for working with AMPL.
"""

import argparse
import json
import sys
import time
from typing import Any

from amplpy import AMPL, ErrorHandler, OutputHandler, modules

# Duration parameter for the solver.
SUPPORTED_PROVIDER_DURATIONS = {
    "cbc": "timelimit",
    "copt": "timelimit",
    "gcg": "timelimit",
    "gurobi": "timelimit",
    "highs": "timelimit",
    "lgo": "timelim",
    "scip": "timelimit",
    "xpress": "timelimit",
}

# Open source solvers.
OSS_SOLVERS = ["cbc", "gcg", "gecode", "highs", "scip"]

# Status of the solver after optimizing.
STATUS = [
    {"lb": 0, "ub": 99, "status": "optimal"},
    {"lb": 100, "ub": 199, "status": "solved?"},
    {"lb": 200, "ub": 299, "status": "infeasible"},
    {"lb": 300, "ub": 399, "status": "unbounded"},
    {"lb": 400, "ub": 499, "status": "limit"},
    {"lb": 500, "ub": 599, "status": "failure"},
]


class CollectOutput(OutputHandler):
    def __init__(self):
        self.buffer = ""

    def output(self, kind, msg):
        self.buffer += msg


output_handler = CollectOutput()


class CollectWarnings(ErrorHandler):
    def __init__(self):
        self.buffer = ""

    def warning(self, exception):
        self.buffer += str(exception)


error_handler = CollectWarnings()


def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve problems with AMPL.")
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
        default="highs",
        help="Solver provider. Default is highs.",
    )
    args = parser.parse_args()

    # Read input "data", solve the problem and write the solution.
    input_data = read_input(args.input)
    log("Solving knapsack problem:")
    log(f"  - items: {len(input_data.get('items', []))}")
    log(f"  - capacity: {input_data.get('weight_capacity', 0)}")
    log(f"  - max duration: {args.duration} seconds")
    solution = solve(input_data, args.duration, args.provider)
    write_output(args.output, solution)


def solve(input_data: dict[str, Any], duration: int, provider: str) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    start_time = time.time()

    # Activate license.
    if provider not in OSS_SOLVERS:
        license = read_license_uuid()
        modules.activate(license)

    # Defines the model.
    ampl = AMPL()
    ampl.set_output_handler(output_handler)
    ampl.set_error_handler(error_handler)
    ampl.eval(
        r"""
        # Sets
        set I; # Set of items.

        # Parameters
        param W >= 0; # Maximum weight capacity.
        param v {I} >= 0; # Value of each item.
        param w {I} >= 0; # Weight of each item.

        # Variables
        var x {I} binary; # 1 if item is selected, 0 otherwise.

        # Objective
        maximize z: sum {i in I} v[i] * x[i];

        # Constraints
        s.t. weight_limit: sum {i in I} w[i] * x[i] <= W;
        """
    )

    # Sets the solver and options.
    ampl.option["solver"] = provider
    if provider in SUPPORTED_PROVIDER_DURATIONS.keys():
        ampl.option[f"{provider}_options"] = f"{SUPPORTED_PROVIDER_DURATIONS[provider]}={duration}"

    # Set the data on the model.
    ampl.set["I"] = [item["id"] for item in input_data["items"]]
    ampl.param["W"] = input_data["weight_capacity"]
    ampl.param["v"] = {item["id"]: item["value"] for item in input_data["items"]}
    ampl.param["w"] = {item["id"]: item["weight"] for item in input_data["items"]}

    # Solves the problem. Verbose mode is turned off to avoid printing to
    # stdout. Only the output should be printed to stdout.
    ampl.solve(verbose=False)
    log(f"AMPL output after solving: {output_handler.buffer}")
    log(f"AMPL errors after solving: {error_handler.buffer}")

    # Convert to solution format.
    value = ampl.get_objective("z")
    chosen_items = []
    if value:
        chosen_items = [item for item in input_data["items"] if ampl.get_variable("x")[item["id"]].value() > 0.9]

    solve_result = ampl.solve_result_num
    status = "unknown"
    for s in STATUS:
        lb = s.get("lb")
        ub = s.get("ub")
        if lb is not None and ub is not None and lb <= solve_result <= ub:
            status = s.get("status")
            break

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "constraints": ampl.get_value("_ncons"),
                "provider": provider,
                "status": status,
                "variables": ampl.get_value("_nvars"),
            },
            "duration": ampl.get_value("_total_solve_time"),
            "value": value.value(),
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


def read_license_uuid() -> str:
    """Reads the license needed to authenticate."""

    with open("ampl_license_uuid") as file:
        return file.read().strip()


if __name__ == "__main__":
    main()
