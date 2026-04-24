import time
from typing import Any

import nextmv
import nextmv_gurobipy as ngp
from gurobipy import GRB


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
    model = ngp.Model(loaded_input.options)

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

    # Build solution dictionary from model
    solution = {}
    for item_data in items:
        solution[item_data["item"]["id"]] = item_data["variable"].X

    # Build metrics dictionary
    solve_duration = time.time() - start_time
    metrics = {
        "solve_duration": model.Runtime,
        "total_duration": solve_duration,
        "objective_value": model.ObjVal if model.Status == 2 else None,
        "status": model.Status,
        "variables": model.NumVars,
        "constraints": model.NumConstrs,
    }

    return solution, metrics


if __name__ == "__main__":
    main()
