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
    )

    input = nextmv.load_local(options=options, path=options.input)

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {input.data.get('weight_capacity', 0)}")

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
    provider = options.provider
    ampl.option["solver"] = provider
    if provider in SUPPORTED_PROVIDER_DURATIONS.keys():
        ampl.option[f"{provider}_options"] = f"{SUPPORTED_PROVIDER_DURATIONS[provider]}={options.duration}"

    # Set the data on the model.
    ampl.set["I"] = [item["id"] for item in input.data["items"]]
    ampl.param["W"] = input.data["weight_capacity"]
    ampl.param["v"] = {item["id"]: item["value"] for item in input.data["items"]}
    ampl.param["w"] = {item["id"]: item["weight"] for item in input.data["items"]}

    # Solves the problem. Verbose mode is turned off to avoid printing to
    # stdout. Only the output should be printed to stdout.
    ampl.solve()

    # Convert to solution format.
    value = ampl.get_objective("z")
    chosen_items = []
    if value:
        chosen_items = [item for item in input.data["items"] if ampl.get_variable("x")[item["id"]].value() > 0.9]

    solve_result = ampl.solve_result_num
    status = "unknown"
    for s in STATUS:
        lb = s.get("lb")
        ub = s.get("ub")
        if lb is not None and ub is not None and lb <= solve_result <= ub:
            status = s.get("status")
            break

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=ampl.get_value("_total_solve_time"),
            value=value.value(),
            custom={
                "status": status,
                "variables": ampl.get_value("_nvars"),
                "constraints": ampl.get_value("_ncons"),
            },
        ),
    )

    return nextmv.Output(
        options=options,
        solution={"items": chosen_items},
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
