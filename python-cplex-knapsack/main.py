import time
from typing import Any

import cplex
import nextmv


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(loaded_input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {loaded_input.data.get('weight_capacity', 0)}")

    solution, metrics = solve(loaded_input, options)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input, options: nextmv.Options) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Creates the problem.
    problem = cplex.Cplex()
    problem.parameters.timelimit.set(options.duration)

    # Get items data
    items_data = loaded_input.data["items"]
    weight_capacity = loaded_input.data["weight_capacity"]

    # Create variable names and types
    var_names = [item["id"] for item in items_data]
    var_types = [problem.variables.type.binary] * len(items_data)

    # Add variables
    problem.variables.add(names=var_names, types=var_types)

    # Extract weights and values
    weights = [item["weight"] for item in items_data]
    values = [item["value"] for item in items_data]

    # Add weight capacity constraint: sum(weight_i * x_i) <= weight_capacity
    problem.linear_constraints.add(
        lin_expr=[cplex.SparsePair(ind=var_names, val=weights)],
        senses=["L"],  # Less than or equal
        rhs=[weight_capacity],
        names=["weight_capacity"],
    )

    # Set objective function: maximize sum(value_i * x_i)
    problem.objective.set_linear(list(zip(var_names, values, strict=True)))
    problem.objective.set_sense(problem.objective.sense.maximize)

    # Solve the problem
    problem.solve()

    # Determine which items were chosen
    solution_values = problem.solution.get_values()
    chosen_items = [items_data[i] for i in range(len(items_data)) if solution_values[i] > 0.9]

    solution = {"items": chosen_items}

    metrics = {
        "run_duration": time.time() - start_time,
        "solver_duration": problem.get_time(),
        "value": problem.solution.get_objective_value(),
        "status": problem.solution.get_status_string(),
        "variables": problem.variables.get_num(),
        "constraints": problem.linear_constraints.get_num(),
        "provider": "cplex",
    }

    return solution, metrics


if __name__ == "__main__":
    main()
