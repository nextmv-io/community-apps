import argparse
import json
import os.path as path
import time

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

    # Parse parameters / options.
    parser = argparse.ArgumentParser(description="Multi-Knapsack Problem Solver")
    parser.add_argument("--input", type=str, default="inputs/", help="Path to input dir (default: inputs/)")
    parser.add_argument("--output", type=str, default="outputs/", help="Path to output dir (default: outputs/)")
    parser.add_argument("--duration", type=int, default=30, help="Max runtime duration in seconds (default: 30)")
    parser.add_argument("--provider", type=str, default="SCIP", help="Solver provider (default: SCIP)")
    args = parser.parse_args()

    # Load input data.
    items_df = pd.read_excel(f"{args.input}/input.xlsx", sheet_name="items")
    knapsacks_df = pd.read_excel(f"{args.input}/input.xlsx", sheet_name="knapsacks")
    solution_file = path.join(args.output, "assignments.xlsx")
    stats_file = "statistics.json"

    print("Solving multi-knapsack problem:")
    print(f"  - items: {len(items_df)}")
    print(f"  - knapsacks: {len(knapsacks_df)}")

    # Solve the problem.
    solution, statistics = solve(items_df, knapsacks_df, args.provider, args.duration)

    # Output the solution.
    print(f"Solution:\n{solution}")
    solution.to_excel(solution_file, index=False, sheet_name="assignments")
    print(f"Solution saved to {solution_file}")

    # Output the statistics.
    with open(stats_file, "w") as f:
        json.dump(statistics, f, indent=4)
    print(f"Statistics saved to {stats_file}")


def solve(
    items_df: pd.DataFrame,
    knapsacks_df: pd.DataFrame,
    provider: str,
    duration: int,
) -> tuple[pd.DataFrame, dict]:
    """Solves the given problem and returns the solution."""

    start_time = time.time()

    # Creates the solver.
    solver = pywraplp.Solver.CreateSolver(provider)
    solver.SetTimeLimit(duration * 1000)

    # Unpack the input data.
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

    statistics = {
        "statistics": {
            "schema": "v1",
            "run": {"duration": time.time() - start_time},
            "result": {
                "duration": solver.WallTime() / 1000,
                "value": solver.Objective().Value(),
                "custom": {
                    "status": STATUS.get(status, "unknown"),
                    "variables": solver.NumVariables(),
                    "constraints": solver.NumConstraints(),
                },
            },
        }
    }

    return pd.DataFrame(
        {
            "knapsack_id": [knapsack_id for knapsack_id, _ in chosen_items],
            "item_id": [item_id for _, item_id in chosen_items],
        }
    ), statistics


if __name__ == "__main__":
    main()
