"""
Template for working with AMPL.
"""

import os
import time
from platform import uname

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

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Parameter("provider", str, "highs", "Solver provider.", False),
        nextmv.Parameter("model", str, ".", "Path to folder containing the .mod file.", False),
    )

    input = nextmv.load_local(options=options, path=options.input)

    nextmv.log("Solving price optimization problem:")
    nextmv.log(f"  - regions: {len(input.data.get('regions', []))}")

    output = solve(input, options)
    nextmv.write_local(output, path=options.output)


def solve(input: nextmv.Input, options: nextmv.Options) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Activate license.
    license_used = activate_license()
    options.license_used = license_used

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
    ampl.set["R"] = input.data["regions"]
    ampl.param["cost_waste"] = input.data["cost_per_wasted_product"]
    ampl.param["cost_transport"] = {r: input.data["transport_costs"][i] for i, r in enumerate(input.data["regions"])}
    ampl.param["price_min"] = input.data["minimum_product_price"]
    ampl.param["price_max"] = input.data["maximum_product_price"]
    ampl.param["quantity_min"] = {
        r: input.data["minimum_product_allocations"][i] for i, r in enumerate(input.data["regions"])
    }
    ampl.param["quantity_max"] = {
        r: input.data["maximum_product_allocations"][i] for i, r in enumerate(input.data["regions"])
    }
    ampl.param["total_amount_of_supply"] = input.data["total_amount_of_supply"]
    ampl.param["coefficients_intercept"] = input.data["coefficients"]["intercept"]
    ampl.param["coefficients_region"] = {
        r: input.data["coefficients"]["region"][i] for i, r in enumerate(input.data["regions"])
    }
    ampl.param["coefficients_price"] = input.data["coefficients"]["price"]
    ampl.param["coefficients_year_index"] = input.data["coefficients"]["year_index"]
    ampl.param["coefficients_peak"] = input.data["coefficients"]["peak"]
    ampl.param["data_year"] = input.data["year"]
    ampl.param["data_peak"] = input.data["peak"]

    # Solves the problem. Verbose mode is turned off to avoid printing to
    # stdout. Only the output should be printed to stdout.
    ampl.solve(verbose=False)

    # Convert to solution format.
    objective_val = ampl.get_objective("obj")
    solution = {}
    if objective_val:
        solution = {
            "regions": input.data["regions"],
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
    coefficients = input.data["coefficients"]
    expected_demand = {}

    for r in range(len(input.data["regions"])):
        expected_demand[input.data["regions"][r]] = round(
            (
                coefficients["intercept"]
                + coefficients["price"] * price_solution[r][1]
                + coefficients["region"][r]
                + coefficients["year_index"] * (input.data["year"] - 2015)
                + coefficients["peak"] * input.data["peak"]
            ),
            8,
        )
    expected_sales = {r: round(ampl.get_variable("sales")[r].value(), 8) for r in ampl.get_set("R")}
    expected_waste = {r: round(ampl.get_variable("waste")[r].value(), 8) for r in ampl.get_set("R")}

    # Convert -0.0 to 0.0
    expected_sales = {r: 0.0 if v == -0.0 else v for r, v in expected_sales.items()}
    expected_waste = {r: 0.0 if v == -0.0 else v for r, v in expected_waste.items()}

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=ampl.get_value("_total_solve_time"),
            value=objective_val.value(),
            custom={
                "status": status,
                "variables": ampl.get_value("_nvars"),
                "constraints": ampl.get_value("_ncons"),
                "expected_demand": expected_demand,
                "expected_sales": expected_sales,
                "expected_waste": expected_waste,
            },
        ),
    )

    return nextmv.Output(
        options=options,
        solution=solution,
        statistics=statistics,
    )


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
