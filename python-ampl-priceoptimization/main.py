import os
import time
from platform import uname
from typing import Any

import nextmv
from amplpy import AMPL, modules

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


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving price optimization problem:")
    nextmv.log(f"  - regions: {len(loaded_input.data.get('regions', []))}")

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    options = loaded_input.options

    # Activate license.
    license_used = activate_license()

    # Defines the model.
    ampl = AMPL()
    ampl.reset()
    ampl.read(f"{options.model}/ampl_model.mod")

    # Sets the solver and options.
    provider = options.provider
    ampl.option["solver"] = provider
    if provider in SUPPORTED_PROVIDER_DURATIONS.keys():
        ampl.option[f"{provider}_options"] = f"{SUPPORTED_PROVIDER_DURATIONS[provider]}={options.duration}"

    # Set the data on the model.
    ampl.set["R"] = loaded_input.data["regions"]
    ampl.param["cost_waste"] = loaded_input.data["cost_per_wasted_product"]
    ampl.param["cost_transport"] = {
        r: loaded_input.data["transport_costs"][i] for i, r in enumerate(loaded_input.data["regions"])
    }
    ampl.param["price_min"] = loaded_input.data["minimum_product_price"]
    ampl.param["price_max"] = loaded_input.data["maximum_product_price"]
    ampl.param["quantity_min"] = {
        r: loaded_input.data["minimum_product_allocations"][i] for i, r in enumerate(loaded_input.data["regions"])
    }
    ampl.param["quantity_max"] = {
        r: loaded_input.data["maximum_product_allocations"][i] for i, r in enumerate(loaded_input.data["regions"])
    }
    ampl.param["total_amount_of_supply"] = loaded_input.data["total_amount_of_supply"]
    ampl.param["coefficients_intercept"] = loaded_input.data["coefficients"]["intercept"]
    ampl.param["coefficients_region"] = {
        r: loaded_input.data["coefficients"]["region"][i] for i, r in enumerate(loaded_input.data["regions"])
    }
    ampl.param["coefficients_price"] = loaded_input.data["coefficients"]["price"]
    ampl.param["coefficients_year_index"] = loaded_input.data["coefficients"]["year_index"]
    ampl.param["coefficients_peak"] = loaded_input.data["coefficients"]["peak"]
    ampl.param["data_year"] = loaded_input.data["year"]
    ampl.param["data_peak"] = loaded_input.data["peak"]

    # Solves the problem. Verbose mode is turned off to avoid printing to
    # stdout. Only the output should be printed to stdout.
    ampl.solve(verbose=False)

    # Convert to solution format.
    objective_val = ampl.get_objective("obj")
    solution = {}
    if objective_val:
        solution = {
            "regions": loaded_input.data["regions"],
            "price": {r: round(ampl.get_variable("price")[r].value(), 2) for r in ampl.get_set("R")},
            "quantity": {r: round(ampl.get_variable("quantity")[r].value(), 8) for r in ampl.get_set("R")},
        }

    solve_result = ampl.solve_result_num
    status = "unknown"
    for s in STATUS:
        lb = s.get("lb")
        ub = s.get("ub")
        if lb is not None and ub is not None and lb <= solve_result <= ub:
            status = s.get("status")
            break

    # calculate expected demand for each region
    price_solution = ampl.getVariable("price").getValues().toList()
    coefficients = loaded_input.data["coefficients"]
    expected_demand = {}

    for r in range(len(loaded_input.data["regions"])):
        expected_demand[loaded_input.data["regions"][r]] = round(
            (
                coefficients["intercept"]
                + coefficients["price"] * price_solution[r][1]
                + coefficients["region"][r]
                + coefficients["year_index"] * (loaded_input.data["year"] - 2015)
                + coefficients["peak"] * loaded_input.data["peak"]
            ),
            8,
        )
    expected_sales = {r: round(ampl.get_variable("sales")[r].value(), 8) for r in ampl.get_set("R")}
    expected_waste = {r: round(ampl.get_variable("waste")[r].value(), 8) for r in ampl.get_set("R")}

    # Convert -0.0 to 0.0
    expected_sales = {r: 0.0 if v == -0.0 else v for r, v in expected_sales.items()}
    expected_waste = {r: 0.0 if v == -0.0 else v for r, v in expected_waste.items()}

    # Create metrics dictionary
    metrics: dict[str, Any] = {
        "run_duration": time.time() - start_time,
        "solve_duration": ampl.get_value("_total_solve_time"),
        "objective_value": objective_val.value(),
        "status": status,
        "variables": ampl.get_value("_nvars"),
        "constraints": ampl.get_value("_ncons"),
        "expected_demand": expected_demand,
        "expected_sales": expected_sales,
        "expected_waste": expected_waste,
        "license_used": license_used,
    }

    return solution, metrics


def activate_license() -> str:
    """
    Activates de AMPL license based on the use case for the app. If there is a
    license configured in the file, and it is different from the template
    message, it activates the license. Otherwise, use a special module if
    running on Nextmv Cloud. No further action required for testing locally.

    Returns:
        str: The license that was activated: "license", "nextmv" or
        "demo".
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


if __name__ == "__main__":
    main()
