import time
from typing import Any

import nextmv
import pandas as pd
from ortools.linear_solver import pywraplp

# Status of the solver after optimizing.
STATUS = {
    pywraplp.Solver.FEASIBLE: "suboptimal",
    pywraplp.Solver.INFEASIBLE: "infeasible",
    pywraplp.Solver.OPTIMAL: "optimal",
    pywraplp.Solver.UNBOUNDED: "unbounded",
    pywraplp.Solver.ABNORMAL: "abnormal",
    pywraplp.Solver.NOT_SOLVED: "not_solved",
    pywraplp.Solver.MODEL_INVALID: "model_invalid",
}


def main() -> None:
    """Entry point for the program."""

    items_input_file = nextmv.DataFile(
        name="items.csv",
        loader=lambda path: pd.read_csv(path),
        input_data_key="items",
    )
    weight_capacity_input_file = nextmv.DataFile(
        name="weight_capacity.csv",
        loader=lambda path: pd.read_csv(path),
        input_data_key="weight_capacity",
    )

    loaded_input = nextmv.load(
        data_files=[items_input_file, weight_capacity_input_file],
    )
    options = loaded_input.options

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(loaded_input.data.get('items', []))}")
    nextmv.log("  - capacity:")
    nextmv.log(loaded_input.data.get("weight_capacity", 0))

    solution_files, metrics = solve(loaded_input, options)
    nextmv.write(solution_files=solution_files, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input, options: nextmv.Options) -> tuple[list[nextmv.SolutionFile], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Unpack the input data.
    items_df: pd.DataFrame = loaded_input.data["items"]
    items = items_df.to_dict("records")

    # Creates the solver.
    solver = pywraplp.Solver.CreateSolver(options.provider)
    solver.SetTimeLimit(options.duration * 1000)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    item_variables = []
    for item in items:
        item_variable = solver.IntVar(0, 1, item["id"])
        item_variables.append({"item": item, "variable": item_variable})
        weights += item_variable * int(item["weight"])
        values += item_variable * int(item["value"])

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    capacity_df: pd.DataFrame = loaded_input.data["weight_capacity"]
    capacity = int(capacity_df.iloc[0]["weight_capacity"])
    solver.Add(weights <= capacity)

    # Sets the objective function: maximize the value of the chosen items.
    solver.Maximize(values)

    # Solves the problem.
    status = solver.Solve()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in item_variables if item["variable"].solution_value() > 0.9]

    # Create metrics.
    metrics = {
        "run_duration": time.time() - start_time,
        "solver_duration": solver.WallTime() / 1000,
        "objective_value": solver.Objective().Value(),
        "status": STATUS.get(status, "unknown"),
        "variables": solver.NumVariables(),
        "constraints": solver.NumConstraints(),
    }

    # Create solution files.
    solution_files = [
        nextmv.csv_solution_file("solution", data=chosen_items),
    ]

    return solution_files, metrics


if __name__ == "__main__":
    main()
