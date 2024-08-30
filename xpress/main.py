"""
Template for working with FICO Xpress.
"""

import time

import nextmv

try:
    import xpress as xp
except ImportError as exc:
    raise ImportError("is xpress available for your OS and ARCH and installed?") from exc


# Status of the solver after optimizing.
STATUS = {
    xp.SolStatus.FEASIBLE: "suboptimal",
    xp.SolStatus.INFEASIBLE: "infeasible",
    xp.SolStatus.OPTIMAL: "optimal",
    xp.SolStatus.UNBOUNDED: "unbounded",
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

    # Creates the problem.
    problem = xp.problem()
    problem.setControl("timelimit", options.duration)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input.data["items"]:
        item_variable = xp.var(vartype=xp.binary, name=item["id"])
        problem.addVariable(item_variable)
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    problem.addConstraint(weights <= input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    problem.setObjective(values, sense=xp.maximize)

    # Solves the problem.
    _, status = problem.optimize()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if problem.getSolution(item["variable"]) > 0.9]

    options.provider = "xpress"
    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=problem.getAttrib("time"),
            value=problem.getAttrib("objval"),
            custom={
                "status": STATUS.get(status, "unknown"),
                "variables": problem.getAttrib("cols"),
                "constraints": problem.getAttrib("rows"),
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
