"""
Template for working with Hexaly.
"""

import time

import nextmv
from hexaly import optimizer
from hexaly.optimizer import HxSolutionStatus

# Status of the solver after optimizing.
STATUS = {
    HxSolutionStatus.OPTIMAL: "optimal",
    HxSolutionStatus.FEASIBLE: "feasible",
    HxSolutionStatus.INCONSISTENT: "inconsistent",
    HxSolutionStatus.INFEASIBLE: "infeasible",
}


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
    solver = optimizer.HexalyOptimizer()
    model = solver.model
    solver.param.time_limit = options.duration

    # Makes the solver write to stderr so that logs show up in Nextmv Console.
    solver.param.verbosity = 1

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input.data["items"]:
        item_variable = model.bool()
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.constraint(weights <= input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.maximize(values)

    # Closes the model and solves the problem.
    model.close()
    solver.solve()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if item["variable"].value > 0.9]

    options.provider = "hexaly"
    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(
            duration=time.time() - start_time,
            iterations=solver.statistics.nb_iterations,
        ),
        result=nextmv.ResultStatistics(
            duration=solver.statistics.get_running_time(),
            value=values.value,
            custom={
                "status": STATUS.get(solver.solution.status, "unknown"),
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
