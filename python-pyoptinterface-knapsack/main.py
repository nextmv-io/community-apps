"""
Template for working with the pyoptinterface library.
"""

import time
from importlib.metadata import version
from typing import Any

import nextmv
import pyoptinterface as poi
from pyoptinterface import highs


def main() -> None:
    """Entry point for the template."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(loaded_input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {loaded_input.data.get('weight_capacity', 0)}")

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start = time.time()

    # Creates the solver.
    model = highs.Model()
    model.set_model_attribute(poi.ModelAttribute.TimeLimitSec, input.options.duration)
    model.set_model_attribute(poi.ModelAttribute.Silent, True)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input.data["items"]:
        item_variable = model.add_variable(
            lb=0.0,
            ub=1.0,
            domain=poi.VariableDomain.Integer,
            name=item["id"],
        )
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.add_linear_constraint(
        expr=weights,
        sense=poi.ConstraintSense.LessEqual,
        rhs=input.data["weight_capacity"],
        name="weight_capacity",
    )

    # Sets the objective function: maximize the value of the chosen items.
    model.set_objective(
        expr=values,
        sense=poi.ObjectiveSense.Maximize,
    )

    # Solves the problem.
    model.optimize()
    status = model.get_model_attribute(poi.ModelAttribute.TerminationStatus)

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if model.get_value(item["variable"]) > 0.9]

    solution = {"items": chosen_items}
    metrics = {
        "duration": time.time() - start,
        "value": sum(item["value"] for item in chosen_items),
        "status": str(status),
        "variables": model.number_of_variables(),
        "constraints": model.number_of_constraints(type=poi.ConstraintType.Linear),
        "pyoptinterface_version": version("pyoptinterface"),
    }

    return solution, metrics


if __name__ == "__main__":
    main()
