import os
import os.path

import nextmv
from hexaly.modeler import HexalyModeler


def main() -> None:
    options = nextmv.Options(
        nextmv.Option("input", str, "inputs/", "input path", False),
        nextmv.Option("output", str, "outputs/solutions/", "output path", False),
        nextmv.Option("duration", int, 30, "max runtime in seconds", False),
    )

    os.makedirs(options.output, exist_ok=True)

    with HexalyModeler() as modeler:
        optimizer = modeler.create_optimizer()
        model_path = find_model(options.input, [".hxm", ".lsp"])
        data_path = find_model(options.input, [".dat"])
        module = modeler.load_module("model", model_path)
        module.run(
            optimizer,
            f"inFileName={data_path}",
            f"solFileName={options.output}/output.txt",
            f"hxTimeLimit={options.duration}",
        )

    with open(f"{options.output}/output.txt") as f:
        nextmv.write(
            nextmv.Output(
                solution=f.read(),
                options=options.to_dict(),
                output_format=nextmv.OutputFormat.MULTI_FILE,
            ),
            path=options.output,
        )


def find_model(path: str, extensions: list[str]) -> str:
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
