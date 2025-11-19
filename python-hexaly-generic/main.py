import os
import shutil
import sys

import nextmv
from hexaly.modeler import HexalyModeler

# Name of the option that makes the app copy all files from the `inputs/` directory to the
# current working directory before running the model. This is on by default as well.
OPTION_UN_NEST = "unNest"


def main() -> None:
    """Entry point for the program."""

    # Parse options from command line arguments.
    options, un_nest = parse_options()
    nextmv.log("Options:")
    for key, value in options.items():
        nextmv.log(f"  - {key}: {value}")

    # If the `unNest=true` option is set, copy all files from the `inputs/` directory to
    # the current working directory.
    if un_nest:
        nextmv.log("Using unNest option, copying files from inputs/ to current directory.")
        unnest_directory("inputs")

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


def parse_options() -> tuple[dict[str, str], bool]:
    """
    Parses all arguments so that they can be submitted to the model. Returns a dictionary
    of options and a boolean indicating whether the inputs directory should be un-nested.
    """
    un_nest = True
    options = {}
    for arg in sys.argv[1:]:
        if arg.startswith("--"):
            arg = arg[2:]
        elif arg.startswith("-"):
            arg = arg[1:]
        if arg == OPTION_UN_NEST:
            un_nest = True
            continue
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key == OPTION_UN_NEST:
                un_nest = True
                continue
            options[key] = value
        else:
            options[arg] = "true"
    return options, un_nest


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
