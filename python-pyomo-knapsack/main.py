import time
from typing import Any

import nextmv
import pyomo.environ as pyo

# Duration parameter for the solver.
SUPPORTED_PROVIDER_DURATIONS = {
    "cbc": "sec",
    "glpk": "tmlim",
    "scip": "limits/time",
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

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(loaded_input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {loaded_input.data.get('weight_capacity', 0)}")

    solution, metrics = solve(loaded_input, options)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input, options: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

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
    item_ids = [item["id"] for item in loaded_input.data["items"]]
    model.item_variable = pyo.Var(item_ids, domain=pyo.Boolean)

    # Use the decision variables for the linear sums
    items = []
    for item in loaded_input.data["items"]:
        item_id = item["id"]
        items.append({"item": item, "variable": model.item_variable[item_id]})
        weights += model.item_variable[item_id] * item["weight"]
        values += model.item_variable[item_id] * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.constraint = pyo.Constraint(expr=weights <= loaded_input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.objective = pyo.Objective(expr=values, sense=pyo.maximize)

    # Solves the problem.
    results = solver.solve(model, tee=False)  # Set tee to True for Pyomo logging.

    # Convert to solution format.
    value = pyo.value(model.objective, exception=False)
    chosen_items = []
    if value:
        chosen_items = [item["item"] for item in items if item["variable"]() > 0.9]

    solution = {"items": chosen_items}

    metrics = {
        "run_duration": time.time() - start_time,
        "result_duration": results.solver.time,
        "result_value": value,
        "status": STATUS.get(results.solver.termination_condition, "unknown"),
        "variables": model.nvariables(),
        "constraints": model.nconstraints(),
    }

    return solution, metrics


if __name__ == "__main__":
    main()
