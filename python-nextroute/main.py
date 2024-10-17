import nextmv
import nextroute


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("solve_duration", int, 30, "Maximum duration, in seconds, of the solver.", False),
        nextmv.Parameter("solve_parallelruns", int, -1, "Max number of parallel runs, -1 uses all resources.", False),
        nextmv.Parameter("solve_iterations", int, -1, "Max number of iterations, -1 assumes no limit.", False),
        nextmv.Parameter("solve_rundeterministically", bool, False, "Whether to run deterministically.", False),
        nextmv.Parameter("solve_startsolutions", int, -1, "Number of solutions on top of initial ones.", False),
        nextmv.Parameter("format_disable_progression", bool, False, "Disable the series data.", False),
        # Add more options if needed.
    )

    input = nextmv.load_local(options=options, path=options.input)

    nextmv.log("Solving vehicle routing problem:")
    nextmv.log(f"  - stops: {len(input.data.get('stops', []))}")
    nextmv.log(f"  - vehicles: {len(input.data.get('vehicles', []))}")

    output = solve(input, options)
    nextmv.write_local(output, path=options.output)


def solve(input: nextmv.Input, options: nextmv.Options) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

    nextroute_input = nextroute.schema.Input.from_dict(input.data)
    nextroute_options = nextroute.Options(
        solve=nextroute.ParallelSolveOptions(
            duration=options.solve_duration,
            iterations=options.solve_iterations,
            parallel_runs=options.solve_parallelruns,
            run_deterministically=options.solve_rundeterministically,
            start_solutions=options.solve_startsolutions,
        ),
        format=nextroute.FormatOptions(
            disable=nextroute.DisableFormatOptions(
                progression=options.format_disable_progression,
            ),
        ),
    )

    nextroute_output = nextroute.solve(nextroute_input, nextroute_options)

    return nextmv.Output(
        options={
            "nextmv": options.to_dict(),
            "nextroute": nextroute_options.to_dict(),
        },
        solution=nextroute_output.solutions[0].to_dict(),
        statistics=nextroute_output.statistics.to_dict(),
    )


if __name__ == "__main__":
    main()
