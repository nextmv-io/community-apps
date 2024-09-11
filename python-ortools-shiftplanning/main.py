import datetime
import time
from typing import Any

import nextmv
from ortools.linear_solver import pywraplp

# Status of the solver after optimizing.
STATUS = {
    pywraplp.Solver.FEASIBLE: "feasible",
    pywraplp.Solver.INFEASIBLE: "infeasible",
    pywraplp.Solver.OPTIMAL: "optimal",
    pywraplp.Solver.UNBOUNDED: "unbounded",
}
ANY_SOLUTION = [pywraplp.Solver.FEASIBLE, pywraplp.Solver.OPTIMAL]


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Parameter("provider", str, "SCIP", "Solver provider.", False),
    )

    input = nextmv.load_local(options=options, path=options.input)

    nextmv.log("Solving shift-planning:")
    nextmv.log(f"  - shifts-templates: {len(input.data.get('shifts', []))}")
    nextmv.log(f"  - demands: {len(input.data.get('demands', []))}")

    output = solve(input, options)
    nextmv.write_local(output, path=options.output)


def solve(input: nextmv.Input, options: nextmv.Options) -> nextmv.Output:
    """Solves the given problem and returns the solution."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Creates the solver.
    solver = pywraplp.Solver.CreateSolver(options.provider)
    solver.SetTimeLimit(options.duration * 1000)

    # Prepare data
    shifts, demands = convert_data(input.data)
    input_options = input.data.get("options", {})

    # Generate concrete shifts from shift templates.
    concrete_shifts = get_concrete_shifts(shifts)

    # Determine all unique time periods in which demands occur and the shifts covering them.
    periods = get_demand_coverage_periods(concrete_shifts, demands)

    # Determine the time we need to cover.
    required_hours = sum((p.end_time - p.start_time).seconds for p in periods) / 3600

    # Create integer variables indicating how many times a shift is planned.
    x_assign = {}
    for s in concrete_shifts:
        x_assign[s["id"]] = solver.IntVar(
            s["min_workers"],
            s["max_workers"] if s["max_workers"] >= 0 else solver.infinity(),
            f'Planned_{s["id"]}',
        )

    # Create variables for tracking various costs.
    if "under_supply_cost" in input_options:
        x_under = {}
        for p in periods:
            x_under[p] = solver.NumVar(0, solver.infinity(), f"UnderSupply_{p}")
        underSupply = solver.NumVar(0, solver.infinity(), "UnderSupply")
    if "over_supply_cost" in input_options:
        overSupply = solver.NumVar(0, solver.infinity(), "OverSupply")
    shift_cost = solver.NumVar(0, solver.infinity(), "ShiftCost")

    # Objective function: minimize the cost of the planned shifts
    obj_expr = solver.Sum([0])
    if "under_supply_cost" in input_options:
        obj_expr += underSupply * input_options["under_supply_cost"]
    if "over_supply_cost" in input_options:
        obj_expr += overSupply * input_options["over_supply_cost"]
    obj_expr += shift_cost
    solver.Minimize(obj_expr)

    # >> Constraints

    # We need to make sure that all demands are covered (or track under supply).
    for p in periods:
        expression = solver.Sum([x_assign[s["id"]] for s in p.covering_shifts])
        if "under_supply_cost" in input_options:
            expression += x_under[p]
        solver.Add(
            expression == sum(d["count"] for d in p.demands),
            f"DemandCover_{p.start_time}_{p.end_time}_{p.qualification}",
        )

    # Track under supply
    if "under_supply_cost" in input_options:
        solver.Add(
            underSupply == solver.Sum([x_under[p] * (p.end_time - p.start_time).seconds / 3600 for p in periods]),
            "UnderSupply",
        )

    # Track over supply
    if "over_supply_cost" in input_options:
        solver.Add(
            overSupply
            == solver.Sum(
                [x_assign[s["id"]] * (s["end_time"] - s["start_time"]).seconds / 3600 for s in concrete_shifts]
            )
            - required_hours,
            "OverSupply",
        )

    # Track shift cost
    solver.Add(
        shift_cost == solver.Sum([x_assign[s["id"]] * s["cost"] for s in concrete_shifts]),
        "ShiftCost",
    )

    # Solves the problem.
    status = solver.Solve()

    # Convert to solution format.
    has_solution = status in ANY_SOLUTION
    schedule = {
        "planned_shifts": [
            {
                "id": s["id"],
                "shift_id": s["shift_id"],
                "time_id": s["time_id"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "qualification": s["qualification"],
                "count": int(round(x_assign[(s["id"])].solution_value())),
            }
            for s in concrete_shifts
            if x_assign[(s["id"])].solution_value() > 0.5
        ]
        if has_solution
        else [],
    }

    under_supply = 0
    over_supply = 0
    under_supply_cost = 0
    over_supply_cost = 0
    value = None
    if has_solution:
        if "under_supply_cost" in input_options:
            under_supply = underSupply.solution_value()
            under_supply_cost = under_supply * input_options["under_supply_cost"]
        if "over_supply_cost" in input_options:
            over_supply = overSupply.solution_value()
            over_supply_cost = over_supply * input_options["over_supply_cost"]

        value = solver.Objective().Value()

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=solver.WallTime() / 1000,
            value=value,
            custom={
                "status": STATUS.get(status, "unknown"),
                "variables": solver.NumVariables(),
                "constraints": solver.NumConstraints(),
                "planned_shifts": len(schedule["planned_shifts"]),
                "planned_count": sum(s["count"] for s in schedule["planned_shifts"]),
                "shift_cost": shift_cost.solution_value() if has_solution else 0,
                "under_supply": under_supply,
                "over_supply": over_supply,
                "over_supply_cost": over_supply_cost,
                "under_supply_cost": under_supply_cost,
            },
        ),
    )

    return nextmv.Output(
        options=options,
        solution=schedule,
        statistics=statistics,
    )


class UniqueQualificationDemandPeriod:
    """
    Represents a unique time-period and qualification combination. It lists all demands
    causing the need for this qualification in this time period, as well as all shifts
    helping in covering them.
    """

    def __init__(
        self,
        start_time: datetime.datetime,
        end_time: datetime.datetime,
        qualification: str,
        covering_shifts: list[str],
        demands: list[str],
    ):
        """Creates a new unique time-period and qualification combination."""

        self.start_time = start_time
        self.end_time = end_time
        self.qualification = qualification
        self.covering_shifts = covering_shifts
        self.demands = demands

    def __str__(self) -> str:
        """Returns a string representation of this object."""

        return f"{self.start_time.isoformat()}_{self.end_time.isoformat()}_{self.qualification}"


def get_concrete_shifts(shifts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    # Convert shift templates into concrete shifts. I.e., for every shift and every time
    # it can be planned, we create a concrete shift.
    # While most characteristics are given on the shift itself (except for the time), many
    # of them can be overwritten by the individual times a shift can be planned. E.g., the
    # maximum number of workers that can be assigned to a shift may be less during a night
    # shift than during a day shift.
    concrete_shifts = [
        {
            "id": f"{shift['id']}_{time['id']}",
            "shift_id": shift["id"],
            "time_id": time["id"],
            "start_time": time["start_time"],
            "end_time": time["end_time"],
            # Min workers is 0 at default. Furthermore, it can be overwritten by the individual time.
            "min_workers": time["min_workers"]
            if "min_workers" in time
            else shift["min_workers"]
            if "min_workers" in shift
            else 0,
            # Max workers is -1 at default (unbounded). Furthermore, it can be overwritten by the individual time.
            "max_workers": time["max_workers"]
            if "max_workers" in time
            else shift["max_workers"]
            if "max_workers" in shift
            else -1,
            # Cost is required. Furthermore, it can be overwritten by the individual time.
            "cost": time["cost"] if "cost" in time else shift["cost"],
            # Make sure that the qualification is present.
            "qualification": shift["qualification"] if "qualification" in shift else "",
        }
        for shift in shifts
        for time in shift["times"]
    ]
    return concrete_shifts


def get_demand_coverage_periods(
    concrete_shifts: list[dict[str, Any]], demands: list[dict[str, Any]]
) -> list[UniqueQualificationDemandPeriod]:
    """
    Determines all unique time-periods with demand for a qualification. It returns all
    demands contributing and all shifts potentially covering this time period.
    """

    # Group demands by their required qualification
    demands_per_qualification = {}
    for d in demands:
        qualification = d["qualification"] if "qualification" in d else ""
        if qualification not in demands_per_qualification:
            demands_per_qualification[qualification] = []
        demands_per_qualification[qualification].append(d)

    # Determine all concrete shifts covering a demand
    shifts_per_qualification = {}
    for q in demands_per_qualification:
        shifts_per_qualification[q] = [s for s in concrete_shifts if q == s["qualification"]]

    # Determine all unique time periods
    periods = []
    for q in demands_per_qualification:
        # Determine all unique times for this qualification
        times = set()
        for d in demands_per_qualification[q]:
            times.add(d["start_time"])
            times.add(d["end_time"])
        for s in shifts_per_qualification[q]:
            times.add(s["start_time"])
            times.add(s["end_time"])
        times = sorted(times)

        # Create unique time periods
        for i in range(len(times) - 1):
            start, end = times[i], times[i + 1]
            # Collect all shifts covering this time period and demands contributing to it
            covering_shifts = [
                s for s in shifts_per_qualification[q] if s["start_time"] <= start and s["end_time"] >= end
            ]
            contributing_demands = [
                d for d in demands_per_qualification[q] if d["start_time"] <= start and d["end_time"] >= end
            ]
            if not any(contributing_demands):
                continue
            periods.append(
                UniqueQualificationDemandPeriod(
                    start,
                    end,
                    q,
                    covering_shifts,
                    contributing_demands,
                )
            )

    return periods


def convert_data(
    input_data: dict[str, Any],
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    """Converts the input data into the format expected by the model."""
    shifts = input_data["shifts"]
    demands = input_data["demands"]
    # In-place convert all times to datetime objects.
    for s in shifts:
        for t in s["times"]:
            t["start_time"] = datetime.datetime.fromisoformat(t["start_time"])
            t["end_time"] = datetime.datetime.fromisoformat(t["end_time"])
    for d in demands:
        d["start_time"] = datetime.datetime.fromisoformat(d["start_time"])
        d["end_time"] = datetime.datetime.fromisoformat(d["end_time"])
        d["qualification"] = d["qualification"] if "qualification" in d else ""
    return shifts, demands


if __name__ == "__main__":
    main()
