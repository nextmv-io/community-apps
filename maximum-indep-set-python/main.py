"""
Main execution file in maximum-independent set problem
"""

import argparse
import json
import logging
import logging.config
import os
from typing import List, Optional

from optimizer import GreedyChoice, MultiRandom, read_input


log = logging.getLogger(__name__)


def setup_logging():
    logs_dir = os.path.join(os.path.dirname(__name__), "logs")
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)

    # Load the logging configuration from the JSON file
    config_path = os.path.join(logs_dir, "config.json")
    if os.path.exists(config_path):
        with open(config_path, "rt") as f:
            config = json.load(f)
        logging.config.dictConfig(config)
    else:
        print(f"Error: Could not find the logging configuration file {config_path}. Using default settings.")


def solve(
    data: dict,
    algo: Optional[str] = None,
    maxiter: int = 1,
    seed: Optional[int] = None
) -> List[int]:
    if algo == "greedy" or algo is None:
        G = GreedyChoice(data["edges"], nodes=data.get("nodes", None))
        G()
    elif algo == "random":
        G = MultiRandom(data["edges"], nodes=data.get("nodes", None), seed=seed)
        G(n_iter=maxiter)
    else:
        raise ValueError(f"Algorithm should be 'greedy' or 'random' - {algo} is invalid")
    sol = G.output
    return sol


def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", "-i",
        default=None,
        dest="input",
        help="Path to input file. Default is stdin.",
    )
    parser.add_argument(
        "-output",
        default=None,
        dest="output",
        help="Path to output file. Default is stdout.",
    )
    parser.add_argument(
        "-algorithm",
        default=None,
        dest="algorithm",
        help="greedy or random",
    )
    parser.add_argument(
        "-seed",
        default=None,
        dest="seed",
        type=int,
        help="Random seed (in case of random choice)",
    )
    parser.add_argument(
        "-maxiter",
        default=1,
        dest="maxiter",
        type=int,
        help="Number of iterations in multistart - Only used in case of RandomChoice",
    )
    args = parser.parse_args()

    # Read input data, solve the problem and write the solution.
    input_data = read_input(args.input)
    log.info("Solving maximum independent set problem problem:")
    solution = solve(input_data)
    solution = solve(input_data, args.algorithm, args.maxiter, args.seed)
    write_output(args.output, solution)


def write_output(output_path, output) -> None:
    """Writes the output to stdout or a given output file."""

    content = json.dumps(output, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
