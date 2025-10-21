#!/usr/bin/env python3

from cuopt import routing
from datetime import datetime
import cudf
import nextmv


SOLUTION_STATUS = {s.value: s.name for s in routing.SolutionStatus}


def main() -> None:
    start = datetime.now()

    options = nextmv.Options(
        nextmv.Option("time_limit", float, default=1),
        nextmv.Option("verbose_mode", bool, default=False),
    )

    data = nextmv.load().data
    distance = cudf.DataFrame(data["distance"], dtype="float32")
    locations = len(distance) - 1

    data_model = routing.DataModel(
        distance.shape[0],
        data["vehicles"],
        locations,
    )

    data_model.add_cost_matrix(distance)
    data_model.add_transit_time_matrix(distance.copy(deep=True))
    data_model.add_capacity_dimension(
        "demand",
        cudf.Series([1] * locations),
        cudf.Series([data["capacity"]] * data["vehicles"]),
    )

    solver_settings = routing.SolverSettings()
    solver_settings.set_time_limit(options.time_limit)
    solver_settings.set_verbose_mode(options.verbose_mode)

    solution = routing.Solve(data_model, solver_settings)

    nextmv.write(
        nextmv.Output(
            options=options,
            solution=solution.route.to_dict(orient="records"),
            statistics=nextmv.Statistics(
                run=nextmv.RunStatistics(
                    duration=(datetime.now() - start).total_seconds(),
                ),
                result=nextmv.ResultStatistics(
                    value=solution.get_total_objective(),
                    custom={
                        "status": SOLUTION_STATUS[solution.get_status()],
                        "vehicle_count": solution.get_vehicle_count(),
                    },
                ),
            ),
        ),
    )


if __name__ == "__main__":
    main()
