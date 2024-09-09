"""
Template for working with the pyoptinterface library.
"""

import time
from importlib.metadata import version

import nextmv
import pyoptinterface as poi
from pyoptinterface import highs


def main() -> None:
    """Entry point for the template."""

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


def solve(input_data: nextmv.Input, options: nextmv.Options) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

    start = time.time()

    # Creates the solver.
    model = highs.Model()
    model.set_model_attribute(poi.ModelAttribute.TimeLimitSec, options.duration)
    model.set_model_attribute(poi.ModelAttribute.Silent, True)

    # Initializes the linear sums.
    weights = 0.0
    values = 0.0

    # Creates the decision variables and adds them to the linear sums.
    items = []
    for item in input_data["items"]:
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
        rhs=input_data["weight_capacity"],
        name="weight_capacity",
    )

    # Sets the objective function: maximize the value of the chosen items.
    status = model.set_objective(
        expr=values,
        sense=poi.ObjectiveSense.Maximize,
    )

    # Solves the problem.
    model.optimize()
    status = model.get_model_attribute(poi.ModelAttribute.TerminationStatus)

    # Determines which items were chosen.
    chosen_items = [item["item"] for item in items if model.get_value(item["variable"]) > 0.9]

    options.version = version("pyoptinterface")

    # Creates the statistics.
    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start),
        result=nextmv.ResultStatistics(
            value=sum(item["value"] for item in chosen_items),
            custom={
                "status": str(status),
                "variables": model.number_of_variables(),
                "constraints": model.number_of_constraints(type=poi.ConstraintType.Linear),
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
