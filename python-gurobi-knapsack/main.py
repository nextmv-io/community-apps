import os
import time

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

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
    )

    input = nextmv.load_local(options=options, path=options.input)

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {input.data.get('weight_capacity', 0)}")

    output = solve(input, options)
    nextmv.write_local(output, path=options.output)


def solve(input: nextmv.Input, options: nextmv.Options) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

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
    model.Params.TimeLimit = options.duration

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input.data["items"]:
        item_variable = model.addVar(vtype=GRB.BINARY, name=item["id"])
        items.append({"item": item, "variable": item_variable})
        weights += item_variable * item["weight"]
        values += item_variable * item["value"]

    # This constraint ensures the weight capacity of the knapsack will not be
    # exceeded.
    model.addConstr(weights <= input.data["weight_capacity"])

    # Sets the objective function: maximize the value of the chosen items.
    model.setObjective(expr=values, sense=GRB.MAXIMIZE)

    # Solves the problem.
    model.optimize()

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if item["variable"].X > 0.9]

    options.provider = "gurobi"
    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=model.Runtime,
            value=model.ObjVal,
            custom={
                "status": STATUS.get(model.Status, "unknown"),
                "variables": model.NumVars,
                "constraints": model.NumConstrs,
            },
        ),
    )

    return nextmv.Output(
        options=options,
        solution={"items": chosen_items},
        statistics=statistics,
    )


if __name__ == "__main__":
    main()
