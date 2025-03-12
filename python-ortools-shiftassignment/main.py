import datetime
import time
from typing import Any

import nextmv
from ortools.linear_solver import pywraplp

# Status of the solver after optimizing.
STATUS = {
    pywraplp.Solver.FEASIBLE: "suboptimal",
    pywraplp.Solver.INFEASIBLE: "infeasible",
    pywraplp.Solver.OPTIMAL: "optimal",
    pywraplp.Solver.UNBOUNDED: "unbounded",
}


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Parameter("provider", str, "SCIP", "Solver provider.", False),
        nextmv.Parameter(
            "factor-maximize-weekly-hours-per-worker",
            float,
            0.0,
            "Weight to apply for maximizing total weekly hours per worker (up to allowed maximum).",
            False,
        ),
        nextmv.Parameter(
            "factor-balance-total-hours",
            float,
            0.0,
            "Weight to apply for balancing worker hours.",
            False,
        ),
        nextmv.Parameter(
            "factor-maximize-preferences",
            float,
            1.0,
            "Weight to apply for total preference matches.",
            False,
        ),
    )

    input = nextmv.load_local(options=options, path=options.input)

    nextmv.log("Solving shift-assignment:")
    nextmv.log(f"  - shifts: {len(input.data.get('shifts', []))}")
    nextmv.log(f"  - workers: {len(input.data.get('workers', []))}")
    nextmv.log(f"  - rules: {len(input.data.get('rules', []))}")

    model = DecisionModel()
    output = model.solve(input)
    nextmv.write_local(output, path=options.output)


class DecisionModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        start_time = time.time()
        nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

        # Creates the solver.
        solver = pywraplp.Solver.CreateSolver(input.options.provider)
        solver.SetTimeLimit(input.options.duration * 1000)

        # Prepare data
        workers, shifts, rules_per_worker, earliest_shift_start_time, latest_shift_end_time = convert_input(input.data)

        # Create binary variables indicating whether an worker is assigned to a shift
        x_assign = {}
        for e in workers:
            for s in shifts:
                x_assign[(e["id"], s["id"])] = solver.BoolVar(f"Assignment_{e['id']}_{s['id']}")

        # Create auxiliary variables for total hours worked by each worker
        total_hours = {}
        for e in workers:
            total_hours[e["id"]] = solver.NumVar(0, solver.infinity(), f"TotalHours_{e['id']}")

        # Create auxiliary variables for deviation from mean hours worked
        deviations = {}
        for e in workers:
            deviations[e["id"]] = solver.NumVar(0, solver.infinity(), f"Deviation_{e['id']}")

        # >>> Constraints

        # Each shift must have the required number of workers
        for s in shifts:
            solver.Add(
                solver.Sum([x_assign[(e["id"], s["id"])] for e in workers]) == s["count"],
                f"Shift_{s['id']}",
            )

        # Each worker must be assigned to at least their minimum number of shifts
        for e in workers:
            rules = rules_per_worker[e["id"]]
            solver.Add(
                solver.Sum([x_assign[(e["id"], s["id"])] for s in shifts]) >= rules["min_shifts"],
                f"worker_{e['id']}",
            )

        # Each worker must be assigned to at most their maximum number of shifts
        for e in workers:
            rules = rules_per_worker[e["id"]]
            solver.Add(
                solver.Sum([x_assign[(e["id"], s["id"])] for s in shifts]) <= rules["max_shifts"],
                f"worker_{e['id']}",
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
                    solver.Add(
                        x_assign[(e["id"], shift1["id"])] + x_assign[(e["id"], shift2["id"])] <= 1,
                        f"Rest_{e['id']}_{shift1['id']}_{shift2['id']}",
                    )

        # Ensure that availabilities are respected
        for e in workers:
            for s in shifts:
                if not any(
                    a["start_time"] <= s["start_time"] and a["end_time"] >= s["end_time"] for a in e["availability"]
                ):
                    x_assign[(e["id"], s["id"])].SetBounds(0, 0)

        # Ensure that workers are qualified for the shift
        for e in workers:
            for s in shifts:
                if "qualification" not in s or s["qualification"] == "":
                    # No qualifications required for shift (worker can be assigned)
                    continue
                if "qualifications" not in e:
                    # A qualification is required for the shift, but the worker has none (worker cannot be assigned)
                    x_assign[(e["id"], s["id"])].SetBounds(0, 0)
                    continue
                if s["qualification"] not in e["qualifications"]:
                    # The worker does not have the required qualification (worker cannot be assigned)
                    x_assign[(e["id"], s["id"])].SetBounds(0, 0)

        # Ensure that the minimum and maximum work hours per day are respected
        for e in workers:
            for day in range((latest_shift_end_time - earliest_shift_start_time).days + 1):
                day_start = earliest_shift_start_time + datetime.timedelta(days=day)
                day_end = day_start + datetime.timedelta(days=1)
                solver.Add(
                    solver.Sum(
                        [
                            x_assign[(e["id"], s["id"])]
                            * ((min(s["end_time"], day_end) - max(s["start_time"], day_start)).total_seconds() / 3600)
                            for s in shifts
                            if s["start_time"] < day_end and s["end_time"] >= day_start
                        ]
                    )
                    <= rules_per_worker[e["id"]]["max_work_hours_per_day"],
                    f"MaxWorkHours_{e['id']}_{day}",
                )
                solver.Add(
                    solver.Sum(
                        [
                            x_assign[(e["id"], s["id"])]
                            * ((min(s["end_time"], day_end) - max(s["start_time"], day_start)).total_seconds() / 3600)
                            for s in shifts
                            if s["start_time"] < day_end and s["end_time"] >= day_start
                        ]
                    )
                    >= rules_per_worker[e["id"]]["min_work_hours_per_day"],
                    f"MinWorkHours_{e['id']}_{day}",
                )
                # Ensure total hours worked by each worker are correctly calculated
                for e in workers:
                    solver.Add(
                        total_hours[e["id"]]
                        == solver.Sum(
                            [
                                x_assign[(e["id"], s["id"])] * (s["end_time"] - s["start_time"]).total_seconds() / 3600
                                for s in shifts
                            ]
                        ),
                        f"TotalHours_{e['id']}",
                    )

        # Ensure that the maximum work hours per week are respected
        for e in workers:
            for week in range((latest_shift_end_time - earliest_shift_start_time).days // 7 + 1):
                week_start = earliest_shift_start_time + datetime.timedelta(weeks=week)
                week_end = week_start + datetime.timedelta(days=7)
                solver.Add(
                    solver.Sum(
                        [
                            x_assign[(e["id"], s["id"])]
                            * ((min(s["end_time"], week_end) - max(s["start_time"], week_start)).total_seconds() / 3600)
                            for s in shifts
                            if s["start_time"] < week_end and s["end_time"] > week_start
                        ]
                    )
                    <= rules_per_worker[e["id"]]["max_work_hours_per_week"],
                    f"MaxWorkHours_{e['id']}_Week{week}",
                )

        # >>> Objective
        objective = solver.Objective()
        preference_weight = input.options.factor_maximize_preferences
        balance_hours_weight = input.options.factor_balance_total_hours
        weekly_hours_weight = input.options.factor_maximize_weekly_hours_per_worker
        avg_hours = solver.Sum([total_hours[e["id"]] for e in workers]) / len(workers)

        for e in workers:
            # Maximize preferences
            for s in shifts:
                pref = e["preferences"].get(s["id"], 0)
                if pref > 0:
                    objective.SetCoefficient(x_assign[(e["id"], s["id"])], pref * preference_weight)

            # Minimize variance in total hours worked
            deviation = total_hours[e["id"]] - avg_hours
            solver.Add(deviations[e["id"]] == deviation)
            objective.SetCoefficient(deviations[e["id"]], -balance_hours_weight)

            # Maximize total hours worked up to the maximum allowed
            objective.SetCoefficient(total_hours[e["id"]], weekly_hours_weight)

        objective.SetMaximization()

        # Solves the problem.
        status = solver.Solve()

        # Convert to solution format.
        schedule = {}
        active_workers, total_workers = 0, 0
        value = None
        if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
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
                    if x_assign[(e["id"], s["id"])].solution_value() > 0.5
                ],
            }
            active_workers = len({s["worker_id"] for s in schedule["assigned_shifts"]})
            total_workers = len(workers)
            value = solver.Objective().Value()
            mean_hours_worked = sum(total_hours[e["id"]].solution_value() for e in workers) / len(workers)
            variance_hours_worked = sum(
                (total_hours[e["id"]].solution_value() - mean_hours_worked) ** 2 for e in workers
            ) / len(workers)
            preferences_matched = sum(
                e["preferences"].get(s["shift_id"], 0)
                for e in workers
                for s in schedule["assigned_shifts"]
                if s["worker_id"] == e["id"]
            )
        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=time.time() - start_time),
            result=nextmv.ResultStatistics(
                duration=solver.WallTime() / 1000,
                value=value,
                custom={
                    "status": STATUS.get(status, "unknown"),
                    "variables": solver.NumVariables(),
                    "constraints": solver.NumConstraints(),
                    "active_workers": active_workers,
                    "total_workers": total_workers,
                    "mean_hours_worked": mean_hours_worked,
                    "variance_hours_worked": variance_hours_worked,
                    "preferences_matched": preferences_matched,
                },
            ),
        )

        return nextmv.Output(
            options=input.options,
            solution=schedule,
            statistics=statistics,
        )


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
        r["min_work_hours_per_day"] = r.get("min_work_hours_per_day", 0)
        r["max_work_hours_per_day"] = r.get("max_work_hours_per_day", 24)
        r["max_work_hours_per_week"] = r.get("max_work_hours_per_week", 24 * 7)

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

    # Calculate earliest shift start time and latest shift end time
    earliest_shift_start_time = min(s["start_time"] for s in shifts)
    earliest_shift_start_time = earliest_shift_start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    latest_shift_end_time = max(s["end_time"] for s in shifts)
    latest_shift_end_time = latest_shift_end_time.replace(hour=23, minute=59, second=59, microsecond=999999)

    return workers, shifts, rules_per_worker, earliest_shift_start_time, latest_shift_end_time


if __name__ == "__main__":
    main()
