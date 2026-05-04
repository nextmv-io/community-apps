from typing import Any

import nextmv
import nextroute


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving vehicle routing problem:")
    nextmv.log(f"  - stops: {len(loaded_input.data.get('stops', []))}")
    nextmv.log(f"  - vehicles: {len(loaded_input.data.get('vehicles', []))}")

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    nextroute_input = nextroute.schema.Input.from_dict(loaded_input.data)
    nextroute_options = nextroute.Options.extract_from_dict(loaded_input.options.to_dict())
    nextroute_output = nextroute.solve(nextroute_input, nextroute_options)

    solution = nextroute_output.solutions[0].to_dict()
    metrics = nextroute_output.statistics.to_dict()

    return solution, metrics


if __name__ == "__main__":
    main()
