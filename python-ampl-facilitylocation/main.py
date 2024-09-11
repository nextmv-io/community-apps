import io
import os
import time
from platform import uname

import nextmv
import pandas as pd
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
        nextmv.Parameter("runpath", str, ".", "Path to the directory with the run file.", False),
        nextmv.Parameter("modelpath", str, ".", "Path to the directory with the model file.", False),
    )

    input = nextmv.load_local(options=options, path=options.input)

    nextmv.log("Solving stochastic facility location problem:")
    nextmv.log(f"  - facilities: {input.data.get('FACILITIES', [])}")
    nextmv.log(f"  - customers: {input.data.get('CUSTOMERS', 0)}")

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
    ampl.read(f"{options.modelpath}/floc_bend.mod")
    ampl.set["FACILITIES"] = input.data["FACILITIES"]
    ampl.set["CUSTOMERS"] = input.data["CUSTOMERS"]
    ampl.set["SCENARIOS"] = input.data["SCENARIOS"]
    ampl.param["prob"] = input.data["prob"]
    ampl.param["fixed_cost"] = pd.read_json(io.StringIO(input.data["fixed_cost"]), orient="table")
    ampl.param["facility_capacity"] = pd.read_json(io.StringIO(input.data["facility_capacity"]), orient="table")
    ampl.param["variable_cost"] = pd.read_json(io.StringIO(input.data["variable_cost"]), orient="table")
    ampl.param["customer_demand"] = pd.read_json(io.StringIO(input.data["customer_demand"]), orient="table")

    # Sets the solver and options.
    provider = options.provider
    ampl.option["solver"] = provider
    if provider in SUPPORTED_PROVIDER_DURATIONS.keys():
        opt_name = f"{provider}_options"
        if not ampl.option[opt_name]:
            ampl.option[opt_name] = ""
        ampl.option[opt_name] += f" {SUPPORTED_PROVIDER_DURATIONS[provider]}={options.duration}"
    solve_output = ampl.get_output(f"include {options.runpath}/floc_bend.run;")

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=ampl.get_value("_total_solve_time"),
            value=round(ampl.get_value("operating_cost"), 6),
            custom={
                "status": ampl.solve_result,
                "variables": ampl.get_value("_nvars"),
                "constraints": ampl.get_value("_ncons"),
            },
        ),
    )

    solution = {
        "facility_open": ampl.get_data("facility_open").to_pandas().to_json(orient="table"),
        "total_cost": ampl.get_value("total_cost"),
        "solve_output": solve_output,
    }

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
