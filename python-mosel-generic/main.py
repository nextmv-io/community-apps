import os
import shutil
import sys
import tempfile
import time
from typing import Any

import nextmv

# Input directory as configured in the app.yaml (multi-file content format).
INPUT_DIR = "inputs"

# Option consumed by this runner. All other options are passed to the model as
# Mosel parameters.
MODEL_FILE_OPTION = "model_file"

# Name of a full Xpress license file (e.g., provided as a secret).
LICENSE_FILE = "xpauth.xpr"


def main() -> None:
    """Entry point for the program."""

    start_time = time.time()

    # Use a full Xpress license, if provided. Otherwise, the community license
    # is used. This needs to happen before importing moselpy.
    setup_license()
    import moselpy as mp

    # Mosel and solver output is logged to stderr.
    nextmv.redirect_stdout()
    mp.config.set_default_stream(mp.StreamType.OUTPUT, "sysfd:2")

    # Parse options from command line arguments.
    options = parse_options()
    model_file = options.pop(MODEL_FILE_OPTION, "")
    nextmv.log("Mosel parameters:")
    for key, value in options.items():
        nextmv.log(f"  - {key}: {value}")

    # Copy all input files to a working directory, so that we can tell apart
    # the files written by the model.
    work_dir = tempfile.mkdtemp(prefix="mosel-")
    shutil.copytree(INPUT_DIR, work_dir, dirs_exist_ok=True)
    before = snapshot(work_dir)

    # Find the model file.
    model_path = os.path.join(work_dir, model_file) if model_file else find_file(work_dir, [".mos", ".bim"])
    if not os.path.isfile(model_path):
        raise FileNotFoundError(f"Model file {model_file} not found in {INPUT_DIR}.")
    nextmv.log(f"Model file: {os.path.relpath(model_path, work_dir)}")

    # Load and run the model. Relative paths in the model resolve against the
    # working directory.
    nextmv.log("Running the model...")
    mp.config.default_working_directory = work_dir
    try:
        if model_path.lower().endswith(".bim"):
            model = mp.load_model(model_path)
            model.run(exec_params=options)
        else:
            model, _ = mp.execute_model(model_path, exec_params=options)
    except RuntimeError as e:
        # Mosel already logged the details (e.g., compilation errors).
        nextmv.log(f"Mosel error: {e}")
        sys.exit(1)
    nextmv.log(f"Execution status: {model.exec_status.name}, exit code: {model.exit_code}")

    # All files created or modified by the model are returned as solutions.
    written = [path for path, mtime in snapshot(work_dir).items() if before.get(path) != mtime]
    solution_files = [copy_solution_file(work_dir, path) for path in sorted(written)]
    nextmv.log(f"Files written by the model: {', '.join(sorted(written)) or 'none'}")

    metrics = {
        "run_duration": time.time() - start_time,
        "model": model.name,
        "exec_status": model.exec_status.name,
        "exit_code": model.exit_code,
        **problem_metrics(model),
    }
    nextmv.write(
        nextmv.Output(
            output_format=nextmv.OutputFormat.MULTI_FILE,
            solution_files=solution_files,
            metrics=metrics,
        ),
    )

    shutil.rmtree(work_dir, ignore_errors=True)
    if model.exec_status != mp.ExecStatus.OK:
        nextmv.log(f"Model execution failed with status {model.exec_status.name}.")
        sys.exit(1)


def setup_license() -> None:
    """Points Xpress to a full license file, if one is available."""
    if os.environ.get("XPAUTH_PATH"):
        return
    for path in [LICENSE_FILE, os.path.join(INPUT_DIR, LICENSE_FILE)]:
        if os.path.isfile(path):
            os.environ["XPAUTH_PATH"] = os.path.abspath(path)
            nextmv.log(f"Using Xpress license file {path}.")
            return
    nextmv.log("No Xpress license file found, using the community license.")


def parse_options() -> dict[str, str]:
    """
    Parses all arguments so that they can be submitted to the model as Mosel
    parameters. Supports `key=value`, `-key=value` and `-key value`. Returns a
    dictionary of option names to values.
    """
    options = {}
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        arg = args[i]
        dashed = arg.startswith("-")
        arg = arg.lstrip("-")
        if "=" in arg:
            key, value = arg.split("=", 1)
        elif dashed and i + 1 < len(args) and (not args[i + 1].startswith("-") or is_number(args[i + 1])):
            key, value = arg, args[i + 1]
            i += 1
        else:
            key, value = arg, "true"
        options[key] = value
        i += 1
    return options


def is_number(value: str) -> bool:
    """Returns whether the given value is a number (e.g., a negative one)."""
    try:
        float(value)
        return True
    except ValueError:
        return False


def snapshot(path: str) -> dict[str, float]:
    """Returns the modification times of all files in the given path."""
    files = {}
    for root, _, names in os.walk(path):
        for name in names:
            full_path = os.path.join(root, name)
            files[os.path.relpath(full_path, path)] = os.path.getmtime(full_path)
    return files


def find_file(path: str, extensions: list[str]) -> str:
    """
    Finds the first file (alphabetically) with the first matching extension in
    the specified path. Looks for files recursively.
    """
    files = sorted(snapshot(path))
    for ext in extensions:
        for file in files:
            if file.lower().endswith(ext):
                return os.path.join(path, file)
    raise FileNotFoundError(f"No model file found in {INPUT_DIR} with endings {extensions}.")


def copy_solution_file(work_dir: str, name: str) -> nextmv.SolutionFile:
    """Creates a solution file that copies the given file to the solutions."""

    def writer(file_path: str, source: str) -> None:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        shutil.copy2(source, file_path)

    return nextmv.SolutionFile(name=name, data=os.path.join(work_dir, name), writer=writer)


def problem_metrics(model: Any) -> dict[str, Any]:
    """Returns information about the optimization problem of the model, if any."""
    status = model.problem_status
    if not status.is_optimization_finished:
        return {}
    metrics = {
        "status": (
            "optimal"
            if status.is_solution_optimal
            else "infeasible"
            if status.is_problem_infeasible
            else "unbounded"
            if status.is_problem_unbounded
            else "suboptimal"
            if status.is_solution_available
            else "unknown"
        ),
    }
    if status.is_solution_available:
        metrics["objective_value"] = model.objective_value
    return metrics


if __name__ == "__main__":
    main()
