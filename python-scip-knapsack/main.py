import time
from importlib.metadata import version

import nextmv
import pyscipopt


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Option("duration", int, 30, "Max runtime duration (in seconds).", False),
    )

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

        # Create the model.
        model = pyscipopt.Model("knapsack")
        # Define variables for assignment of items to the knapsack.
        x = []
        for item in input.data["items"]:
            x.append(model.addVar(vtype="B", obj=item["value"]))
        # Define constraint respecting the weight capacity of the knapsack.
        model.addCons(
            sum(x[i] * item["weight"] for i, item in enumerate(input.data["items"])) <= input.data["weight_capacity"]
        )
        # Maximize the total value of the knapsack.
        model.setMaximize()

        # Solve the model.
        model.setParam("limits/time", input.options.duration)
        model.setParam("display/verblevel", 0)  # suppress output to support clean json on stdout
        model.optimize()

        # Determine which items were chosen.
        chosen_items = [item["id"] for i, item in enumerate(input.data["items"]) if model.getVal(x[i]) > 0.5]

        # Prepare the output.
        input.options.version = version("pyscipopt")
        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=time.time() - start_time),
            result=nextmv.ResultStatistics(
                value=model.getObjVal(),
                custom={
                    "status": str(model.getStatus()),
                    "variables": model.getNVars(),
                    "constraints": model.getNConss(),
                },
            ),
        )

        return nextmv.Output(
            options=input.options,
            solution={"items": chosen_items},
            statistics=statistics,
        )


if __name__ == "__main__":
    main()
