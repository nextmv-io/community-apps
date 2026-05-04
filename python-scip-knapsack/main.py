import time
from importlib.metadata import version
from typing import Any

import nextmv
import pyscipopt


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
    options = loaded_input.options

    # Create the model.
    model = pyscipopt.Model("knapsack")
    # Define variables for assignment of items to the knapsack.
    x = []
    for item in loaded_input.data["items"]:
        x.append(model.addVar(vtype="B", obj=item["value"]))
    # Define constraint respecting the weight capacity of the knapsack.
    model.addCons(
        sum(x[i] * item["weight"] for i, item in enumerate(loaded_input.data["items"]))
        <= loaded_input.data["weight_capacity"]
    )
    # Maximize the total value of the knapsack.
    model.setMaximize()
    n_vars, n_cons = model.getNVars(), model.getNConss()

    # Solve the model.
    model.setParam("limits/time", options.duration)
    model.setParam("display/verblevel", 0)  # suppress output to support clean json on stdout
    model.optimize()

    # Determine which items were chosen.
    chosen_items = [item for i, item in enumerate(loaded_input.data["items"]) if model.getVal(x[i]) > 0.5]

    solution = {"items": chosen_items}
    metrics = {
        "duration": time.time() - start_time,
        "value": model.getObjVal(),
        "status": str(model.getStatus()),
        "variables": n_vars,
        "constraints": n_cons,
        "version": version("pyscipopt"),
    }

    return solution, metrics


if __name__ == "__main__":
    main()
