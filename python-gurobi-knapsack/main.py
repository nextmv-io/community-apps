import os
import time
from typing import Any

import gurobipy as gp
import nextmv
from gurobipy import GRB

# Status of the solver after optimizing.
STATUS = {
    GRB.SUBOPTIMAL: "suboptimal",
    GRB.INFEASIBLE: "infeasible",
    GRB.OPTIMAL: "optimal",
    GRB.UNBOUNDED: "unbounded",
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

    # Creates the environment.
    env = gp.Env(empty=True)

    # Read the license file, if available.
    if os.path.isfile("gurobi.lic"):
        env.readParams("gurobi.lic")

    # Creates the model.
    env.start()
    model = gp.Model(env=env)
    model.Params.TimeLimit = loaded_input.options.duration

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in loaded_input.data["items"]:
        item_variable = model.addVar(vtype=GRB.BINARY, name=item["id"])
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.addConstr(weights <= loaded_input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.setObjective(expr=values, sense=GRB.MAXIMIZE)

    # Solves the problem.
    model.optimize()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if item["variable"].X > 0.9]

    solution = {"items": chosen_items}

    metrics = {
        "run_duration": time.time() - start_time,
        "result_duration": model.Runtime,
        "result_value": model.ObjVal,
        "status": STATUS.get(model.Status, "unknown"),
        "variables": model.NumVars,
        "constraints": model.NumConstrs,
        "provider": "gurobi",
    }

    return solution, metrics


if __name__ == "__main__":
    main()
