"""
Template for working with Hexaly.
"""

import time
from typing import Any

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

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(loaded_input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {loaded_input.data.get('weight_capacity', 0)}")

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Creates the solver.
    solver = optimizer.HexalyOptimizer()
    model = solver.model
    solver.param.time_limit = loaded_input.options.duration

    # Makes the solver write to stderr so that logs show up in Nextmv Console.
    solver.param.verbosity = 1

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in loaded_input.data["items"]:
        item_variable = model.bool()
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.constraint(weights <= loaded_input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.maximize(values)

    # Closes the model and solves the problem.
    model.close()
    solver.solve()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if item["variable"].value > 0.9]

    loaded_input.options.provider = "hexaly"

    solution = {"items": chosen_items}
    metrics = {
        "run_duration": time.time() - start_time,
        "iterations": solver.statistics.nb_iterations,
        "result_duration": solver.statistics.get_running_time(),
        "value": values.value,
        "status": STATUS.get(solver.solution.status, "unknown"),
    }

    return solution, metrics


if __name__ == "__main__":
    main()
