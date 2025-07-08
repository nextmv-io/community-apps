import time

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

    options = nextmv.Options(
        nextmv.Option("input", str, "inputs/", "Path to input file.", False),
        nextmv.Option("output", str, "outputs/", "Path to output file.", False),
        nextmv.Option("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Option("provider", str, "SCIP", "Solver provider.", False),
    )

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

    input = nextmv.load(
        options=options,
        path=options.input,
        data_files=[items_input_file, knapsacks_input_file],
        input_format=nextmv.InputFormat.MULTI_FILE,
    )

    nextmv.log("Solving multi-knapsack problem:")
    nextmv.log(f"  - items: {len(input.data.get('items', []))}")
    nextmv.log(f"  - knapsacks: {len(input.data.get('knapsacks', []))}")

    model = DecisionModel()
    output = model.solve(input)
    nextmv.write(
        output,
        path=options.output,
    )


class DecisionModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        start_time = time.time()
        nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

        # Creates the solver.
        solver = pywraplp.Solver.CreateSolver(input.options.provider)
        solver.SetTimeLimit(input.options.duration * 1000)

        # Unpack the input data.
        if "items" not in input.data or "knapsacks" not in input.data:
            raise ValueError("Input data must contain items and knapsacks.")
        items_df: pd.DataFrame = input.data["items"]
        knapsacks_df: pd.DataFrame = input.data["knapsacks"]
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

        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=time.time() - start_time),
            result=nextmv.ResultStatistics(
                duration=solver.WallTime() / 1000,
                value=solver.Objective().Value(),
                custom={
                    "status": STATUS.get(status, "unknown"),
                    "variables": solver.NumVariables(),
                    "constraints": solver.NumConstraints(),
                },
            ),
        )

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

        return nextmv.Output(
            options=input.options,
            solution_files=[excel_sol_file, csv_sol_file],
            statistics=statistics,
            output_format=nextmv.OutputFormat.MULTI_FILE,
        )


if __name__ == "__main__":
    main()
