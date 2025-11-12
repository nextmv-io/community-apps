import time

import cplex
import nextmv


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
        nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

        # Creates the problem.
        problem = cplex.Cplex()
        problem.parameters.timelimit.set(input.options.duration)

        # Get items data
        items_data = input.data["items"]
        weight_capacity = input.data["weight_capacity"]

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
        solution = problem.solution.get_values()
        chosen_items = [items_data[i] for i in range(len(items_data)) if solution[i] > 0.9]

        input.options.provider = "cplex"
        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=time.time() - start_time),
            result=nextmv.ResultStatistics(
                duration=problem.get_time(),
                value=problem.solution.get_objective_value(),
                custom={
                    "status": problem.solution.get_status_string(),
                    "variables": problem.variables.get_num(),
                    "constraints": problem.linear_constraints.get_num(),
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
