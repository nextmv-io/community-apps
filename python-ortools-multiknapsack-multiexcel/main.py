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
        name="input.xlsx",
        loader=lambda path: pd.read_excel(path, sheet_name="items"),
        input_data_key="items",
    )
    knapsacks_input_file = nextmv.DataFile(
        name="input.xlsx",
        loader=lambda path: pd.read_excel(path, sheet_name="knapsacks"),
        input_data_key="knapsacks",
    )

    loaded_input = nextmv.load(
        data_files=[items_input_file, knapsacks_input_file],
    )
    options = loaded_input.options

    nextmv.log("Solving multi-knapsack problem:")
    nextmv.log(f"  - items: {len(loaded_input.data.get('items', []))}")
    nextmv.log(f"  - knapsacks: {len(loaded_input.data.get('knapsacks', []))}")

    solution, metrics = solve(loaded_input)
    nextmv.write(
        solution_files=solution,
        metrics=metrics,
        options=options,
    )


def solve(loaded_input: nextmv.Input) -> tuple[list[nextmv.SolutionFile], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Creates the solver.
    solver = pywraplp.Solver.CreateSolver(loaded_input.options.provider)
    solver.SetTimeLimit(loaded_input.options.duration * 1000)

    # Unpack the input data.
    if "items" not in loaded_input.data or "knapsacks" not in loaded_input.data:
        raise ValueError("Input data must contain items and knapsacks.")
    items_df: pd.DataFrame = loaded_input.data["items"]
    knapsacks_df: pd.DataFrame = loaded_input.data["knapsacks"]
    items = items_df.to_dict("records")
    knapsacks = knapsacks_df.to_dict("records")

    # Initialize variables.
    assignments = {}
    for knapsack in knapsacks:
        for item in items:
            # Create a binary variable for each item in each knapsack.
            assignments[(knapsack["id"], item["id"])] = solver.IntVar(0, 1, f"{knapsack['id']}_{item['id']}")

    # Make sure the knapsacks' capacities are not exceeded.
    for knapsack in knapsacks:
        solver.Add(
            solver.Sum(assignments[(knapsack["id"], item["id"])] * item["weight"] for item in items)
            <= knapsack["capacity"]
        )

    # Ensure that each item can only be assigned once.
    for item in items:
        solver.Add(solver.Sum(assignments[(knapsack["id"], item["id"])] for knapsack in knapsacks) <= 1)

    # Maximize the total value of the items in the knapsacks.
    solver.Maximize(
        solver.Sum(
            assignments[(knapsack["id"], item["id"])] * item["value"] for knapsack in knapsacks for item in items
        )
    )

    # Solves the problem.
    status = solver.Solve()

    # Determines which items were chosen.
    chosen_items = [
        (knapsack["id"], item["id"])
        for knapsack in knapsacks
        for item in items
        if assignments[(knapsack["id"], item["id"])].solution_value() > 0.5
    ]

    metrics = {
        "run_duration": time.time() - start_time,
        "solver_duration": solver.WallTime() / 1000,
        "value": solver.Objective().Value(),
        "status": STATUS.get(status, "unknown"),
        "variables": solver.NumVariables(),
        "constraints": solver.NumConstraints(),
    }

    excel_sol_file = nextmv.SolutionFile(
        name="assignments.xlsx",
        data=pd.DataFrame(
            {
                "knapsack_id": [knapsack_id for knapsack_id, _ in chosen_items],
                "item_id": [item_id for _, item_id in chosen_items],
            }
        ),
        writer=lambda path, data: data.to_excel(path, index=False, sheet_name="assignments"),
    )
    csv_sol_file = nextmv.csv_solution_file(
        "assignments",
        data=[{"knapsack_id": knapsack_id, "item_id": item_id} for knapsack_id, item_id in chosen_items],
    )

    return [excel_sol_file, csv_sol_file], metrics


if __name__ == "__main__":
    main()
