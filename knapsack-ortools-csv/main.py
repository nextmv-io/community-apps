"""
Template for working with Google OR-Tools.
"""

import time

import nextmv
from ortools.linear_solver import pywraplp

# Status of the solver after optimizing.
STATUS = {
    pywraplp.Solver.FEASIBLE: "suboptimal",
    pywraplp.Solver.INFEASIBLE: "infeasible",
    pywraplp.Solver.OPTIMAL: "optimal",
    pywraplp.Solver.UNBOUNDED: "unbounded",
    pywraplp.Solver.ABNORMAL: "abnormal",
    pywraplp.Solver.NOT_SOLVED: "not_solved",
    pywraplp.Solver.MODEL_INVALID: "model_invalid",
}


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input folder.", False),
        nextmv.Parameter("output", str, "", "Path to output folder.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Parameter("provider", str, "SCIP", "Solver provider.", False),
    )

    input = nextmv.load_local(
        input_format=nextmv.InputFormat.CSV_ARCHIVE,
        options=options,
        path=options.input,
    )

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {input.data.get('weight_capacity', 0)}")

    output = solve(input, options)
    nextmv.write_local(output, path=options.output)


def solve(input: nextmv.Input, options: nextmv.Options) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Creates the solver.
    solver = pywraplp.Solver.CreateSolver(options.provider)
    solver.SetTimeLimit(options.duration * 1000)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input.data["items"]:
        item_variable = solver.IntVar(0, 1, item["id"])
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    capacity = input.data["weight_capacity"][0]["weight_capacity"]  # Read as a CSV.
    solver.Add(weights <= capacity)

    # Sets the objective function: maximize the value of the chosen items.
    solver.Maximize(values)

    # Solves the problem.
    status = solver.Solve()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if item["variable"].solution_value() > 0.9]

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=solver.WallTime() / 1000,
            value=solver.Objective().Value(),
            custom={
                "status": STATUS.get(status, "unknown"),
                "variables": solver.NumVariables(),
                "constraints": solver.NumConstraints(),
            },
        ),
    )

    return nextmv.Output(
        output_format=nextmv.OutputFormat.CSV_ARCHIVE,
        options=options,
        solution={"solution": chosen_items},  # The key is the file name.
        statistics=statistics,
    )


if __name__ == "__main__":
    main()
