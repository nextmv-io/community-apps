import os
import time
from typing import Any

import nextmv

# The Mosel model bundled with the app.
MODEL_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "knapsack.mos")

# Options with this prefix are Xpress controls (e.g., xprs_maxtime). They are
# passed as control parameters of the mmxprs module. All other options are
# passed to the model as Mosel parameters (upper-cased, e.g., max_items sets
# MAX_ITEMS).
SOLVER_OPTION_PREFIX = "xprs_"

# Name of a full Xpress license file (e.g., provided as a secret).
LICENSE_FILE = "xpauth.xpr"


def main() -> None:
    """Entry point for the program."""

    # Use a full Xpress license, if provided. Otherwise, the community license
    # is used. This needs to happen before importing moselpy.
    setup_license()

    # The options are defined in the app.yaml.
    manifest = nextmv.Manifest.from_yaml(os.path.dirname(MODEL_FILE))
    options = manifest.extract_options()
    loaded_input = nextmv.load(options=options)

    nextmv.log("Solving knapsack problem:")
    nextmv.log(f"  - items: {len(loaded_input.data.get('items', []))}")
    nextmv.log(f"  - capacity: {loaded_input.data.get('weight_capacity', 0)}")

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.
    import moselpy as mp

    mp.config.set_default_stream(mp.StreamType.OUTPUT, "sysfd:2")

    # Pass the data to the model.
    items = {item["id"]: item for item in input.data["items"]}
    input_data = {
        "VALUE": {id: item["value"] for id, item in items.items()},
        "WEIGHT": {id: item["weight"] for id, item in items.items()},
        "WEIGHT_CAPACITY": input.data["weight_capacity"],
    }

    # Pass the options (if set) as model parameters and solver controls.
    exec_params = {}
    for key, value in input.options.to_dict().items():
        if value is None:
            continue
        if key.startswith(SOLVER_OPTION_PREFIX):
            exec_params[f"mmxprs.{key}"] = value
        else:
            exec_params[key.upper()] = value
    nextmv.log("Mosel parameters:")
    for key, value in exec_params.items():
        nextmv.log(f"  - {key}: {value}")

    # Solves the problem.
    model, results = mp.execute_model(MODEL_FILE, exec_params=exec_params, input_data=input_data)
    if model.exec_status != mp.ExecStatus.OK:
        raise RuntimeError(f"Model execution failed with status {model.exec_status.name}.")

    # Determines which items were chosen.
    chosen_items = [item for id, item in items.items() if id in results["CHOSEN"]]

    metrics = {
        "duration": time.time() - start_time,
        "solver_duration": results["SOLVER_DURATION"],
        "value": results["OBJECTIVE"],
        "status": results["STATUS"],
        "provider": "xpress",
    }

    return {"items": chosen_items}, metrics


def setup_license() -> None:
    """Points Xpress to a full license file, if one is available."""
    if os.environ.get("XPAUTH_PATH"):
        return
    if os.path.isfile(LICENSE_FILE):
        os.environ["XPAUTH_PATH"] = os.path.abspath(LICENSE_FILE)
        nextmv.log(f"Using Xpress license file {LICENSE_FILE}.")
        return
    nextmv.log("No Xpress license file found, using the community license.")


if __name__ == "__main__":
    main()
