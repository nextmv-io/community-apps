import os
import shutil
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

    # Find the model file in the specified path.
    model_path = find_file(".", [".hxm", ".lsp"])
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
    Parses all arguments so that they can be submitted to the model. Returns a dictionary
    of options and a boolean indicating whether the inputs directory should be un-nested.
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
            options[arg] = "true"
    return options


def unnest_directory(source_directory: str) -> None:
    """
    Copies all files from the source directory to the current working directory.
    """
    # Iterate over all the items in the source directory
    for root, _, files in os.walk(source_directory):
        for file in files:
            # Construct the full file path
            source_file_path = os.path.join(root, file)
            # Copy the file to the current directory
            shutil.copy2(source_file_path, ".")


def find_file(path: str, extensions: list[str]) -> str:
    """
    Finds the first file with the given extension in the specified path. Looks for files
    recursively.
    """
    endings = [ext.lower() for ext in extensions]
    for root, _, files in os.walk(path):
        for file in files:
            if any(file.lower().endswith(ending) for ending in endings):
                return os.path.join(root, file)
    raise FileNotFoundError(f"No model file found in {path} with endings {endings}.")


if __name__ == "__main__":
    main()
