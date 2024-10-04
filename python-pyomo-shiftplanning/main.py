import datetime
import time
from typing import Any

import nextmv
import pyomo.environ as pyo

# Duration parameter for the solver.
SUPPORTED_PROVIDER_DURATIONS = {
    "cbc": "sec",
    "glpk": "tmlim",
    "scip": "limits/time",
}

# Status of the solver after optimizing.
STATUS = {
    pyo.TerminationCondition.feasible: "suboptimal",
    pyo.TerminationCondition.infeasible: "infeasible",
    pyo.TerminationCondition.optimal: "optimal",
    pyo.TerminationCondition.unbounded: "unbounded",
}


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Parameter("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Parameter("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Parameter("duration", int, 30, "Max runtime duration (in seconds).", False),
        nextmv.Parameter("provider", str, "cbc", "Solver provider.", False),
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

    # Make sure the provider is supported.
    provider = options.provider
    if provider not in SUPPORTED_PROVIDER_DURATIONS:
        raise ValueError(
            f"Unsupported provider: {provider}. The supported providers are: "
            f"{', '.join(SUPPORTED_PROVIDER_DURATIONS.keys())}"
        )

    # Create the Pyomo model
    model = pyo.ConcreteModel()

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
    model.x_assign = pyo.Var([(s["id"],) for s in concrete_shifts], within=pyo.NonNegativeIntegers)

    # Bound assignment variables by the minimum and maximum number of workers.
    for s in concrete_shifts:
        model.x_assign[s["id"]].setlb(s["min_workers"])
        if s["max_workers"] >= 0:
            model.x_assign[s["id"]].setub(s["max_workers"])

    # Create variables for tracking various costs.
    if "under_supply_cost" in input_options:
        model.x_under = pyo.Var([(p,) for p in periods], within=pyo.NonNegativeIntegers)
        model.underSupply = pyo.Var(within=pyo.NonNegativeIntegers)
    if "over_supply_cost" in input_options:
        model.overSupply = pyo.Var(within=pyo.NonNegativeIntegers)
    model.shift_cost = pyo.Var(within=pyo.NonNegativeIntegers)

    # Objective function: minimize the cost of the planned shifts
    obj_expr = 0
    if "under_supply_cost" in input_options:
        obj_expr += sum(model.x_under[p] for p in periods) * input_options["under_supply_cost"]
    if "over_supply_cost" in input_options:
        obj_expr += model.overSupply * input_options["over_supply_cost"]
    obj_expr += model.shift_cost
    model.objective = pyo.Objective(expr=obj_expr, sense=pyo.minimize)

    # Constraints

    # We need to make sure that all demands are covered (or track under supply).
    for p in periods:
        constraint_name = f"DemandCover_{p.start_time}_{p.end_time}_{p.qualification}"
        # Add the new constraint
        model.add_component(
            constraint_name,
            pyo.Constraint(
                expr=sum([model.x_assign[s["id"]] for s in p.covering_shifts]) == sum(d["count"] for d in p.demands)
            ),
        )

    # Track under supply
    if "under_supply_cost" in input_options:
        model.under_supply = pyo.Constraint(
            expr=model.underSupply
            == sum(model.x_under[p] * (p.end_time - p.start_time).seconds / 3600 for p in periods)
        )

    # Track over supply
    if "over_supply_cost" in input_options:
        model.over_supply = pyo.Constraint(
            expr=model.overSupply
            == sum(model.x_assign[s["id"]] * (s["end_time"] - s["start_time"]).seconds / 3600 for s in concrete_shifts)
            - required_hours
        )

    # Track shift cost
    model.shift_cost_track = pyo.Constraint(
        expr=model.shift_cost == sum(model.x_assign[s["id"]] * s["cost"] for s in concrete_shifts)
    )

    # Creates the solver.
    solver = pyo.SolverFactory(provider)
    solver.options[SUPPORTED_PROVIDER_DURATIONS[provider]] = options.duration

    # Solve the model.
    results = solver.solve(model, tee=False)  # Set tee to True for Pyomo logging.

    # Convert to solution format.
    val = pyo.value(model.objective, exception=False)
    schedule = {
        "planned_shifts": [
            {
                "id": s["id"],
                "shift_id": s["shift_id"],
                "time_id": s["time_id"],
                "start_time": s["start_time"],
                "end_time": s["end_time"],
                "qualification": s["qualification"],
                "count": int(round(model.x_assign[s["id"]].value)),
            }
            for s in concrete_shifts
            if model.x_assign[s["id"]].value > 0.5
        ]
        if val
        else [],
    }

    under_supply = 0
    over_supply = 0
    under_supply_cost = 0
    over_supply_cost = 0
    if val:
        if "under_supply_cost" in input_options:
            under_supply = model.underSupply()
            under_supply_cost = under_supply * input_options["under_supply_cost"]
        if "over_supply_cost" in input_options:
            over_supply = model.overSupply()
            over_supply_cost = over_supply * input_options["over_supply_cost"]

    statistics = nextmv.Statistics(
        run=nextmv.RunStatistics(duration=time.time() - start_time),
        result=nextmv.ResultStatistics(
            duration=results.solver.time,
            value=val,
            custom={
                "status": STATUS.get(results.solver.termination_condition, "unknown"),
                "variables": model.nvariables(),
                "constraints": model.nconstraints(),
                "planned_shifts": len(schedule["planned_shifts"]),
                "planned_count": sum(s["count"] for s in schedule["planned_shifts"]),
                "shift_cost": model.shift_cost() if val else 0.0,
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
