import time
from typing import Any

import nextmv
import xpress as xp

# Status of the solver after optimizing.
STATUS = {
    xp.SolStatus.FEASIBLE: "suboptimal",
    xp.SolStatus.INFEASIBLE: "infeasible",
    xp.SolStatus.OPTIMAL: "optimal",
    xp.SolStatus.UNBOUNDED: "unbounded",
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


def solve(input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Creates the problem.
    problem = xp.problem()
    problem.setControl("timelimit", input.options.duration)

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

    metrics = {
        "duration": time.time() - start_time,
        "solver_duration": problem.getAttrib("time"),
        "value": problem.getAttrib("objval"),
        "status": STATUS.get(status, "unknown"),
        "variables": problem.getAttrib("cols"),
        "constraints": problem.getAttrib("rows"),
        "provider": "xpress",
    }

    return {"items": chosen_items}, metrics


if __name__ == "__main__":
    main()
