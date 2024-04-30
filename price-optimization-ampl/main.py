"""
Template for working with AMPL.
"""

import argparse
import json
import os
import sys
import time
from platform import uname
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
    log("Solving price optimization problem:")
    log(f"  - regions: {len(input_data.get('regions', []))}")
    log(f"  - max duration: {args.duration} seconds")
    solution = solve(input_data, args.duration, args.provider)
    write_output(args.output, solution)


def solve(input_data: dict[str, Any], duration: int, provider: str) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    start_time = time.time()

    # Activate license.
    license_used = activate_license()

    # Defines the model.
    ampl = AMPL()
    ampl.set_output_handler(output_handler)
    ampl.set_error_handler(error_handler)
    ampl.reset()
    ampl.eval(
        r"""

        # Sets
        set R; # Set of regions.

        # Parameters
        param cost_waste; # Cost per wasted product.
        param cost_transport {R}; # Cost of transport to each region.
        param price_min; # Minimum price for the product.
        param price_max; # Maximum price for the product.
        param quantity_min {R}; # Minimum quantity for each region.
        param quantity_max {R}; # Maximum quantity for each region.
        param total_amount_of_supply; # Total amount of supply.
        param coefficients_intercept; # Intercept of the product demand model.
        param coefficients_region {R}; # Region coefficients of the product demand model.
        param coefficients_price; # Price coefficient of the product demand model.
        param coefficients_year_index; # Year index coefficient of the product demand model.
        param coefficients_peak; # Peak coefficient of the product demand model.
        param data_year; # Year of the data.
        param data_peak; # Peak of the data.

      # Define the demand function
        var demand_expr {r in R} :=
            coefficients_intercept +
            coefficients_region[r] +
            coefficients_price * price[r] +
            coefficients_year_index * (data_year - 2015) +
            coefficients_peak * data_peak;

      # Variables
        var price {r in R} >= price_min, <= price_max;
        var quantity {r in R} >= quantity_min[r], <= quantity_max[r];
        var waste {r in R} := quantity[r] - demand_expr[r];
        var revenue {r in R} := sales_expr[r] * price[r];
        var costs {r in R} := cost_waste * waste[r] + cost_transport[r] * quantity[r];


       # Objective
      # TODO: Gurobi one uses quadratic objective.
        maximize obj: sum {r in regions} revenue[r] - cost[r];

      # Supply constraint checks that the sum of the quantities is equal to the total supply
        subject to supply: sum {r in regions} quantity[r] = total_amount_of_supply;

      # Sales quantity constraints check that the sales are less than or equal
      # to the quantity and demand of the product.
        subject to sales_expr {r in R}: demand_expr[r] <= quantity[r];      """
    )

    # Sets the solver and options.
    ampl.option["solver"] = provider
    if provider in SUPPORTED_PROVIDER_DURATIONS.keys():
        ampl.option[f"{provider}_options"] = f"{SUPPORTED_PROVIDER_DURATIONS[provider]}={duration}"

    # Set the data on the model.
    ampl.set["R"] = input_data["regions"]
    ampl.param["cost_waste"] = input_data["cost_per_wasted_product"]
    ampl.param["cost_transport"] = {r: input_data["transport_costs"][i] for i, r in enumerate(input_data["regions"])}
    ampl.param["price_min"] = input_data["minimum_product_price"]
    ampl.param["price_max"] = input_data["maximum_product_price"]
    ampl.param["quantity_min"] = {
        r: input_data["minimum_product_allocations"][i] for i, r in enumerate(input_data["regions"])
    }
    ampl.param["quantity_max"] = {
        r: input_data["maximum_product_allocations"][i] for i, r in enumerate(input_data["regions"])
    }
    ampl.param["total_amount_of_supply"] = input_data["total_amount_of_supply"]
    ampl.param["coefficients_intercept"] = input_data["coefficients"]["intercept"]
    ampl.param["coefficients_region"] = {
        r: input_data["coefficients"]["region"][i] for i, r in enumerate(input_data["regions"])
    }
    ampl.param["coefficients_price"] = input_data["coefficients"]["price"]
    ampl.param["coefficients_year_index"] = input_data["coefficients"]["year_index"]
    ampl.param["coefficients_peak"] = input_data["coefficients"]["peak"]
    ampl.param["data_year"] = input_data["year"]
    ampl.param["data_peak"] = input_data["peak"]

    # Solves the problem. Verbose mode is turned off to avoid printing to
    # stdout. Only the output should be printed to stdout.
    ampl.solve(verbose=False)
    log(f"AMPL output after solving: {output_handler.buffer}")
    log(f"AMPL errors after solving: {error_handler.buffer}")

    # Convert to solution format.
    # objective_val = ampl.get_objective("obj")
    solutions = []
    # if objective_val:
    # append to solutions the regions, price and quantity.
    solutions.append(
        {
            "regions": input_data["regions"],
            "price": {r: ampl.get_variable("price")[r].value() for r in ampl.get_set("R")},
            "quantity": {r: ampl.get_variable("quantity")[r].value() for r in ampl.get_set("R")},
        }
    )

    solve_result = ampl.solve_result_num
    status = "unknown"
    for s in STATUS:
        lb = s.get("lb")
        ub = s.get("ub")
        if lb is not None and ub is not None and lb <= solve_result <= ub:
            status = s.get("status")
            break

    # TODO: Calculate expected demand, sales, and waste per region.

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
            # "value": objective_val.value(),
        },
        "run": {
            "duration": time.time() - start_time,
            "custom": {
                "license_used": license_used,
            },
        },
        "schema": "v1",
    }

    return {
        "solutions": solutions,
        "statistics": statistics,
    }


def activate_license() -> str:
    """
    Activates de AMPL license based on the use case for the app. If there is a
    license configured in the file, and it is different from the template
    message, it activates the license. Otherwise, use a special module if
    running on Nextmv Cloud. No further action required for testing locally.

    Returns:
        str: The license that was activated: "license", "nextmv" or
        "not_activated".
    """

    # Check if the ampl_license_uuid file exists. NOTE: When running in Nextmv
    # Cloud with a valid license, make sure to run on a premium execution
    # class. Contact support for more information.
    if os.path.isfile("ampl_license_uuid"):
        with open("ampl_license_uuid") as file:
            license = file.read().strip()

        # If the license is not the template message, activate it.
        if license != "secret-key-123":
            modules.activate(license)
            return "license"

    # A valid AMPL license has not been configured. When running on Nextmv
    # Cloud, use a special module.
    system_info = uname()
    if system_info.system == "Linux" and "aarch64" in system_info.machine:
        modules.activate("nextmv")
        return "nextmv"

    return "demo"


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
