import time
from typing import Any

import nextmv
import numpy as np
import pandas as pd
from tsp import getPath, tspModel


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(loaded_input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    options = loaded_input.options
    max_nodes = options.maxnodes
    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.
    city_data = loaded_input.data
    nextmv.log("Solving Traveling Salesman problem:")
    nextmv.log(f"   - Number of nodes: {len(city_data)}")
    nextmv.log(f"   - Solving for >{max_nodes}< nodes")

    city_df = pd.json_normalize(city_data)
    city_df = city_df[["row.city", "row.latitude", "row.longitude"]]

    def euclidean_distance_matrix(coords):
        diff = coords[:, np.newaxis, :] - coords[np.newaxis, :, :]
        dist_matrix = np.sqrt(np.sum(diff**2, axis=-1))
        return dist_matrix

    dist_mat = euclidean_distance_matrix(city_df[["row.latitude", "row.longitude"]].to_numpy())
    dist_df = pd.DataFrame(dist_mat, index=city_df["row.city"], columns=city_df["row.city"])
    distance_df = dist_df.reset_index().melt(id_vars="row.city", var_name="to_city", value_name="distance")

    [sol, tot_time], model = tspModel(nodes_recs=city_df, distance_recs=distance_df, maxnodes=max_nodes)

    path = getPath(sol)

    metrics = {
        "run_duration": time.time() - start_time,
        "solver_duration": tot_time,
        "objective_value": model.objective_value,
        "status": model.status.name,
        "variables": model.num_variables,
        "constraints": model.num_equations,
        "solution_path": " -> ".join(path),
    }

    solution = {
        "solution": sol.to_dict(),
        "total_distance": model.objective_value,
    }

    return solution, metrics


if __name__ == "__main__":
    main()
