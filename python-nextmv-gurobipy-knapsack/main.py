import time

import nextmv
import nextmv_gurobipy as ngp
from gurobipy import GRB


def main() -> None:
    """Entry point for the program."""

    opt = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
    )
    gp_opt = ngp.ModelOptions().to_nextmv()
    options = opt.merge(gp_opt)

    input = nextmv.load(options=options, path=options.input)

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {input.data.get('weight_capacity', 0)}")

    model = DecisionModel()
    output = model.solve(input)
    nextmv.write(output, path=options.output)


class DecisionModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        start_time = time.time()
        model = ngp.Model(input.options)

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

        return nextmv.Output(
            options=input.options,
            solution=ngp.ModelSolution(model),
            statistics=ngp.ModelStatistics(model, start_time),
        )


if __name__ == "__main__":
    main()
