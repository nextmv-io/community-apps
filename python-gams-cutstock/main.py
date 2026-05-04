import time
from typing import Any

import nextmv
from cutstock import cutStockModel


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    solution, metrics = solve(loaded_input, options)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input, options: nextmv.Options) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    max_pattern = options.max_pattern
    raw_width = options.raw_width
    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    demand = dict(zip(loaded_input.data["ID"], loaded_input.data["demand"], strict=False))
    width = dict(zip(loaded_input.data["ID"], loaded_input.data["width"], strict=False))

    nextmv.log("Solving Cutting Stock Problem:")
    nextmv.log(f"-   Number of Materials: {len(demand)}")

    start = time.time()
    [patternFlag, list_of_new_patterns], obj_val, cuts = cutStockModel(
        d=demand, w=width, r=raw_width, max_pattern=max_pattern
    )
    solve_duration = round(time.time() - start, 2)
    total_duration = time.time() - start_time

    solution = {
        "solution": cuts,
    }

    metrics = {
        "duration": total_duration,
        "solve_duration": solve_duration,
        "objective_value": obj_val,
        "new_patterns": list_of_new_patterns,
        "requires_more_pattern": patternFlag,
    }

    return solution, metrics


if __name__ == "__main__":
    main()
