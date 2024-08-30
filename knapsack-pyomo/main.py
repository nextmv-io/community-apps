"""
Template for working with Pyomo.
"""

import time

import nextmv
import pyomo.environ as pyo

# Duration parameter for the solver.
SUPPORTED_PROVIDER_DURATIONS = {
    "cbc": "sec",
    "glpk": "tmlim",
}


# Status of the solver after optimizing.
STATUS = {
    pyo.TerminationCondition.feasible: "suboptimal",
    pyo.TerminationCondition.infeasible: "infeasible",
    pyo.TerminationCondition.optimal: "optimal",
    pyo.TerminationCondition.unbounded: "unbounded",
}


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Parameter("provider", str, "cbc", "Solver provider.", False),
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

    # Make sure the provider is supported.
    provider = options.provider
    if provider not in SUPPORTED_PROVIDER_DURATIONS:
        raise ValueError(
            f"Unsupported provider: {provider}. The supported providers are: "
            f"{', '.join(SUPPORTED_PROVIDER_DURATIONS.keys())}"
        )

    # Creates the model.
    model = pyo.ConcreteModel()

    # Creates the solver.
    solver = pyo.SolverFactory(provider)
    solver.options[SUPPORTED_PROVIDER_DURATIONS[provider]] = options.duration

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables.
    item_ids = [item["id"] for item in input.data["items"]]
    model.item_variable = pyo.Var(item_ids, domain=pyo.Boolean)

    # Use the decision variables for the linear sums
    items = []
    for item in input.data["items"]:
        item_id = item["id"]
        items.append({"item": item, "variable": model.item_variable[item_id]})
        weights += model.item_variable[item_id] * item["weight"]
        values += model.item_variable[item_id] * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.constraint = pyo.Constraint(expr=weights <= input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.objective = pyo.Objective(expr=values, sense=pyo.maximize)

    # Solves the problem.
    results = solver.solve(model)

    # Convert to solution format.
    value = pyo.value(model.objective, exception=False)
    chosen_items = []
    if value:
        chosen_items = [item["item"] for item in items if item["variable"]() > 0.9]

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=results.solver.time,
            value=value,
            custom={
                "status": STATUS.get(results.solver.termination_condition, "unknown"),
                "variables": model.nvariables(),
                "constraints": model.nconstraints(),
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
