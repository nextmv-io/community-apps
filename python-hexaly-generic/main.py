import os
import sys

import nextmv
from hexaly.modeler import HexalyModeler


def main() -> None:
    """Entry point for the program."""

    # Parse options from command line arguments.
    options = parse_options()
    nextmv.log("Options:")
    for key, value in options.items():
        nextmv.log(f"  - {key}: {value}")

    # Make sure the output directory exists.
    os.makedirs(os.path.join("outputs", "solutions"), exist_ok=True)

    # Find the model file in the specified path.
    model_path = find_file("inputs", [".hxm", ".lsp"])
    nextmv.log(f"Model file found: {model_path}")

    # Prepare options for consumption by the model.
    options_list = [f"{key}={value}" for key, value in options.items()]

    # Load and solve the model.
    nextmv.log("Loading and solving the model...")
    with HexalyModeler() as modeler:
        optimizer = modeler.create_optimizer()
        module = modeler.load_module("model", model_path)
        module.run(
            optimizer,
            *options_list,
        )

    nextmv.log("Done.")


def parse_options() -> dict[str, str]:
    """
    Parses all arguments so that they can be submitted to the model.
    """
    options = {}
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            arg = arg[2:]
        elif arg.startswith("-"):
            arg = arg[1:]
        if "=" in arg:
            key, value = arg.split("=", 1)
            options[key] = value
        else:
            options[arg] = True
    return options


def find_file(path: str, extensions: list[str]) -> str:
    """
    Finds the first file with the given extension in the specified path.
    """
    endings = [ext.lower() for ext in extensions]
    for ending in endings:
        for file in os.listdir(path):
            if file.lower().endswith(ending):
                return os.path.join(path, file)
    raise FileNotFoundError(f"No model file found in {path} with endings {endings}.")


if __name__ == "__main__":
    main()
