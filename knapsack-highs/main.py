"""
Template for working with highspy.
"""

import time
from importlib.metadata import version

import highspy
import nextmv


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
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

    # Creates the solver.
    solver = highspy.Highs()
    solver.silent()  # Solver output ignores stdout redirect, silence it.
    solver.setOptionValue("time_limit", options.duration)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input.data["items"]:
        item_variable = solver.addVariable(0.0, 1.0, item["value"])
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    solver.addConstr(weights <= input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    status = solver.maximize(values)

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if solver.val(item["variable"]) > 0.9]

    options.version = version("highspy")

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            value=sum(item["value"] for item in chosen_items),
            custom={
                "status": str(status),
                "variables": solver.numVariables,
                "constraints": solver.numConstrs,
            },
        ),
    )

    return nextmv.Output(
        options=options,
        solution={"items": chosen_items},
        statistics=statistics,
    )


if __name__ == "__main__":
    main()
