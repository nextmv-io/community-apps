#!/usr/bin/env python3
import math
import time
import zoneinfo
from datetime import datetime, timedelta
from itertools import groupby
from operator import itemgetter
from typing import Any

import nextmv
from ortools.linear_solver import pywraplp

BLOCKS = {
    "morning": {
        "hours": "09:00",
        "hours_int": 9,
        "length": 4,
    },
    "midday": {
        "hours": "13:00",
        "hours_int": 13,
        "length": 4,
    },
    "evening": {
        "hours": "17:00",
        "hours_int": 17,
        "length": 4,
    },
    "night": {
        "hours": "21:00",
        "hours_int": 21,
        "length": 12,
    },
}
STATUS = {
    pywraplp.Solver.FEASIBLE: "suboptimal",
    pywraplp.Solver.INFEASIBLE: "infeasible",
    pywraplp.Solver.OPTIMAL: "optimal",
    pywraplp.Solver.UNBOUNDED: "unbounded",
    pywraplp.Solver.ABNORMAL: "abnormal",
    pywraplp.Solver.NOT_SOLVED: "not_solved",
    pywraplp.Solver.MODEL_INVALID: "model_invalid",
}


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    nextmv.log("Solving demand forecasting problem:")
    nextmv.log(f"  - demands: {len(loaded_input.data.get('demands', []))}")

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_timer = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    options = loaded_input.options
    solver = pywraplp.Solver.CreateSolver(options.provider)
    solver.SetTimeLimit(options.duration * 1000)

    # Use a custom bigM, since solver.infinity() causes abnormal termination.
    bigm = 100000000

    timezone_name = loaded_input.data["timezone"]
    demands = loaded_input.data["demands"]
    for i in demands:
        i["demand"] = int(i["demand"])

    block_vars = {}
    for block in BLOCKS.keys():
        block_vars[block] = {
            "offset": solver.NumVar(-bigm, bigm, f"{block}[offset]"),
            "daily": solver.NumVar(-bigm, bigm, f"{block}[daily]"),
            "seasonal_cos": solver.NumVar(-bigm, bigm, f"{block}[seasonal_cos"),
            "seasonal_sin": solver.NumVar(-bigm, bigm, f"{block}[seasonal_sin"),
            "solar_cos": solver.NumVar(-bigm, bigm, f"{block}[solar_cos"),
            "solar_sin": solver.NumVar(-bigm, bigm, f"{block}[solar_sin"),
            "weekly_cos": solver.NumVar(-bigm, bigm, f"{block}[weekly_cos"),
            "weekly_sin": solver.NumVar(-bigm, bigm, f"{block}[weekly_sin"),
        }

    fittings = []
    residuals = []
    for i, (_, group) in enumerate(groupby(demands, itemgetter("date"))):
        for g in group:
            subscript = f"[{i}][{g['block']}]"
            fitted = solver.NumVar(-bigm, bigm, f"fitted{subscript}")
            residual = solver.NumVar(0, bigm, f"residual{subscript}")

            fittings.append(fitted)
            residuals.append(residual)

            a = 2.0 * math.pi * i
            x = block_vars[g["block"]]
            solver.Add(
                fitted
                == x["offset"]
                + (i * x["daily"])
                + (math.cos(a / 365.25) * x["seasonal_cos"])
                + (math.sin(a / 365.25) * x["seasonal_sin"])
                + (math.cos(a / (10.66 * 365.25)) * x["solar_cos"])
                + (math.sin(a / (10.66 * 365.25)) * x["solar_sin"])
                + (math.cos(a / 7) * x["weekly_cos"])
                + (math.sin(a / 7) * x["weekly_sin"])
            )

            solver.Add(residual >= g["demand"] - fitted)
            solver.Add(residual >= fitted - g["demand"])

    solver.Minimize(sum(residuals))
    status = solver.Solve()

    # Add fitted data into training set.
    for i, f in zip(demands, fittings, strict=False):
        i["forecast"] = f.solution_value()

    # Forecast unknown demand.
    forecast = []
    date = datetime.strptime(demands[-1]["date"], "%Y-%m-%d")
    for i in range(28):
        j = (len(demands) / len(BLOCKS)) + i
        for block in BLOCKS.keys():
            a = 2.0 * math.pi * j
            x = block_vars[block]
            y = (
                x["offset"].solution_value()
                + (j * x["daily"].solution_value())
                + (math.cos(a / 365.25) * x["seasonal_cos"].solution_value())
                + (math.sin(a / 365.25) * x["seasonal_sin"].solution_value())
                + (math.cos(a / (10.66 * 365.25)) * x["solar_cos"].solution_value())
                + (math.sin(a / (10.66 * 365.25)) * x["solar_sin"].solution_value())
                + (math.cos(a / 7) * x["weekly_cos"].solution_value())
                + (math.sin(a / 7) * x["weekly_sin"].solution_value())
            )

            date = date.replace(tzinfo=zoneinfo.ZoneInfo(timezone_name))
            start_time = date + timedelta(hours=BLOCKS[block]["hours_int"])
            end_time = start_time + timedelta(hours=BLOCKS[block]["length"])

            forecast.append(
                {
                    "when": f"{date.strftime('%Y-%m-%d')} {BLOCKS[block]['hours']}",
                    "date": date.strftime("%Y-%m-%d"),
                    "block": block,
                    "forecast": y,
                    # Output for next stage
                    "start_time": start_time.isoformat(),
                    "end_time": end_time.isoformat(),
                    "count": int(math.ceil(y)),
                }
            )
        date += timedelta(days=1)

    metrics = {
        "run_duration": time.time() - start_timer,
        "solver_duration": solver.WallTime() / 1000,
        "objective_value": solver.Objective().Value(),
        "status": STATUS.get(status, "unknown"),
        "variables": solver.NumVariables(),
        "constraints": solver.NumConstraints(),
    }

    solution = demands + forecast if options.include_past else forecast

    return solution, metrics


if __name__ == "__main__":
    main()
