import argparse
import datetime
import json
import logging
import sys
from typing import Any

import pyomo.environ as pyo

# Duration parameter for the solver.
SUPPORTED_PROVIDER_DURATIONS = {
    "cbc": "sec",
    "glpk": "tmlim",
}

# Status of the solver after optimizing.
STATUS = {
    pyo.TerminationCondition.feasible: "suboptimal",
    pyo.TerminationCondition.infeasible: "infeasible",
    pyo.TerminationCondition.optimal: "optimal",
    pyo.TerminationCondition.unbounded: "unbounded",
}


def main() -> None:
    """Entry point for the app."""

    parser = argparse.ArgumentParser(description="Solve shift-assignment with Pyomo.")
    parser.add_argument(
        "-input",
        default="",
        help="Path to input file. Default is stdin.",
    )
    parser.add_argument(
        "-output",
        default="",
        help="Path to output file. Default is stdout.",
    )
    parser.add_argument(
        "-duration",
        default=30,
        help="Max runtime duration (in seconds). Default is 30.",
        type=int,
    )
    parser.add_argument(
        "-provider",
        default="cbc",
        help="Solver provider. Default is cbc.",
    )
    args = parser.parse_args()

    # Read input data, solve the problem and write the solution.
    input_data = read_input(args.input)
    log("Solving shift-assignment:")
    log(f"  - shifts: {len(input_data.get('shifts', []))}")
    log(f"  - workers: {len(input_data.get('workers', []))}")
    log(f"  - rules: {len(input_data.get('rules', []))}")
    log(f"  - max duration: {args.duration} seconds")
    solution = solve(input_data, args.duration, args.provider)
    write_output(args.output, solution)


def solve(input_data: dict[str, Any], duration: int, provider: str) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    # Make sure the provider is supported.
    if provider not in SUPPORTED_PROVIDER_DURATIONS:
        raise ValueError(
            f"Unsupported provider: {provider}. The supported providers are: "
            f"{', '.join(SUPPORTED_PROVIDER_DURATIONS.keys())}"
        )

    # Silence all Pyomo logging.
    logging.getLogger("pyomo.core").setLevel(logging.ERROR)

    # Prepare data
    workers, shifts, rules_per_worker = convert_input(input_data)

    # Create binary variables indicating whether a worker is assigned to a shift
    model = pyo.ConcreteModel()
    model.x_assign = pyo.Var(
        [(e["id"], s["id"]) for e in workers for s in shifts],
        within=pyo.Binary,
    )

    # >>> Constraints

    # Each shift must have the required number of workers
    for s in shifts:
        model.add_component(
            f"Shift_{s['id']}",
            pyo.Constraint(expr=sum(model.x_assign[(e["id"], s["id"])] for e in workers) == s["count"]),
        )

    # Each worker must be assigned to at least their minimum number of shifts
    for e in workers:
        rules = rules_per_worker[e["id"]]
        model.add_component(
            f"worker_{e['id']}_min",
            pyo.Constraint(expr=sum(model.x_assign[(e["id"], s["id"])] for s in shifts) >= rules["min_shifts"]),
        )

    # Each worker must be assigned to at most their maximum number of shifts
    for e in workers:
        rules = rules_per_worker[e["id"]]
        model.add_component(
            f"worker_{e['id']}_max",
            pyo.Constraint(expr=sum(model.x_assign[(e["id"], s["id"])] for s in shifts) <= rules["max_shifts"]),
        )

    # Ensure that the minimum rest time between shifts is respected
    for e in workers:
        rest_time = datetime.timedelta(hours=rules_per_worker[e["id"]]["min_rest_hours_between_shifts"])
        for s1, shift1 in enumerate(shifts):
            for s2, shift2 in enumerate(shifts):
                if s1 >= s2:
                    continue
                if (
                    shift1["end_time"] + rest_time < shift2["start_time"]
                    or shift2["end_time"] + rest_time < shift1["start_time"]
                ):
                    continue
                # The two shifts are closer to each other than the minimum rest time, so we need to ensure that
                # the worker is not assigned to both.
                model.add_component(
                    f"Rest_{e['id']}_{shift1['id']}_{shift2['id']}",
                    pyo.Constraint(
                        expr=model.x_assign[(e["id"], shift1["id"])] + model.x_assign[(e["id"], shift2["id"])] <= 1
                    ),
                )

    # Ensure that availabilities are respected
    for e in workers:
        for s in shifts:
            if not any(
                a["start_time"] <= s["start_time"] and a["end_time"] >= s["end_time"] for a in e["availability"]
            ):
                model.x_assign[(e["id"], s["id"])].fix(0)

    # Ensure that workers are qualified for the shift
    for e in workers:
        for s in shifts:
            if "qualification" not in s or s["qualification"] == "":
                # No qualifications required for shift (worker can be assigned)
                continue
            if "qualifications" not in e:
                # A qualification is required for the shift, but the worker has none (worker cannot be assigned)
                model.x_assign[(e["id"], s["id"])].fix(0)
                continue
            if s["qualification"] not in e["qualifications"]:
                # The worker does not have the required qualification (worker cannot be assigned)
                model.x_assign[(e["id"], s["id"])].fix(0)

    # >>> Objective
    model.objective = pyo.Objective(
        expr=sum(
            e["preferences"].get(s["id"], 0) * model.x_assign[(e["id"], s["id"])] for e in workers for s in shifts
        ),
        sense=pyo.maximize,
    )

    # Creates the solver.
    solver = pyo.SolverFactory(provider)  # Use an appropriate solver name
    solver.options[SUPPORTED_PROVIDER_DURATIONS[provider]] = duration

    # Solve the model.
    results = solver.solve(model)

    # Convert to solution format.
    schedule = {}
    active_workers, total_workers = 0, 0
    value = pyo.value(model.objective, exception=False)
    if value:
        schedule = {
            "assigned_shifts": [
                {
                    "start_time": s["start_time"],
                    "end_time": s["end_time"],
                    "worker_id": e["id"],
                    "shift_id": s["id"],
                }
                for e in workers
                for s in shifts
                if model.x_assign[(e["id"], s["id"])].value > 0.5
            ],
        }
        active_workers = len({s["worker_id"] for s in schedule["assigned_shifts"]})
        total_workers = len(workers)

    # Creates the statistics.
    statistics = {
        "result": {
            "custom": {
                "provider": provider,
                "status": STATUS.get(results.solver.termination_condition, "unknown"),
                "variables": model.nvariables(),
                "constraints": model.nconstraints(),
                "active_workers": active_workers,
                "total_workers": total_workers,
            },
            "duration": results.solver.time,
            "value": value,
        },
        "run": {
            "duration": results.solver.time,
        },
        "schema": "v1",
    }

    log(f"  - status: {statistics['result']['custom']['status']}")
    log(f"  - value: {statistics['result']['value']}")
    log(f"  - active workers: {statistics['result']['custom']['active_workers']}")
    log(f"  - total workers: {statistics['result']['custom']['total_workers']}")

    return {
        "solutions": [schedule],
        "statistics": statistics,
    }


def convert_input(input_data: dict[str, Any]) -> tuple[list, list, dict]:
    """Converts the input data to the format expected by the model."""
    workers = input_data["workers"]
    shifts = input_data["shifts"]

    # In-place convert timestamps to datetime objects
    for s in shifts:
        s["start_time"] = datetime.datetime.fromisoformat(s["start_time"])
        s["end_time"] = datetime.datetime.fromisoformat(s["end_time"])
    for e in workers:
        for a in e["availability"]:
            a["start_time"] = datetime.datetime.fromisoformat(a["start_time"])
            a["end_time"] = datetime.datetime.fromisoformat(a["end_time"])

    # Add default values for rules
    for r in input_data["rules"]:
        r["min_shifts"] = r.get("min_shifts", 0)
        r["max_shifts"] = r.get("max_shifts", 1000)

    # Add default values for workers
    for e in workers:
        e["preferences"] = e.get("preferences", {})

    # Merge availabilities of workers that start right where another one ends
    for e in workers:
        e["availability"] = sorted(e["availability"], key=lambda x: x["start_time"])
        i = 0
        while i < len(e["availability"]) - 1:
            if e["availability"][i]["end_time"] == e["availability"][i + 1]["start_time"]:
                e["availability"][i]["end_time"] = e["availability"][i + 1]["end_time"]
                del e["availability"][i + 1]
            else:
                i += 1

    # Convert rules to dict
    rules_per_worker = {}
    for e in workers:
        rule = [r for r in input_data.get("rules", {}) if r["id"] == e["rules"]]
        if len(rule) != 1:
            raise ValueError(f"Invalid rule for worker {e['id']}")
        rules_per_worker[e["id"]] = rule[0]

    return workers, shifts, rules_per_worker


def custom_serial(obj):
    """JSON serializer for objects not serializable by default serializer."""
    if isinstance(obj, (datetime.datetime | datetime.date)):
        return obj.isoformat()
    raise TypeError("Type %s not serializable" % type(obj))


def log(message: str) -> None:
    """Logs a message. We need to use stderr since stdout is used for the solution."""
    print(message, file=sys.stderr)


def read_input(input_path) -> dict[str, Any]:
    """Reads the input from stdin or a given input file."""
    input_file = {}
    if input_path:
        with open(input_path, encoding="utf-8") as file:
            input_file = json.load(file)
    else:
        input_file = json.load(sys.stdin)
    return input_file


def write_output(output_path, output) -> None:
    """Writes the output to stdout or a given output file."""
    content = json.dumps(output, indent=2, default=custom_serial)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
