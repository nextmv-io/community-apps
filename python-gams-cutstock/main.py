import time

import nextmv
from cutstock import cutStockModel


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("raw_width", int, 100, "Total width of a pattern", False),
        nextmv.Option("max_pattern", int, 35, "Maximum possible pattern", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
    )

    input = nextmv.load(options=options, path=options.input)

    model = CutStockModel()
    output = model.solve(input)
    nextmv.write(output, path=options.output)


class CutStockModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        max_pattern = input.options.max_pattern
        raw_width = input.options.raw_width
        start_time = time.time()
        nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

        demand = dict(zip(input.data["ID"], input.data["demand"], strict=False))
        width = dict(zip(input.data["ID"], input.data["width"], strict=False))

        nextmv.log("Solving Cutting Stock Problem:")
        nextmv.log(f"-   Number of Materials: {len(demand)}")

        start = time.time()
        [patternFlag, list_of_new_patterns], obj_val, cuts = cutStockModel(
            d=demand, w=width, r=raw_width, max_pattern=max_pattern
        )
        tot_time = round(time.time() - start, 2)

        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=time.time() - start_time),
            result=nextmv.ResultStatistics(
                duration=tot_time,
                value=f"{obj_val}",
                custom={
                    "New Patterns": f"{list_of_new_patterns}",
                    "Requires more Pattern": f"{patternFlag}",
                },
            ),
        )

        return nextmv.Output(
            options=input.options,
            solution={
                "solution": cuts,
            },
            statistics=statistics,
        )


if __name__ == "__main__":
    main()
