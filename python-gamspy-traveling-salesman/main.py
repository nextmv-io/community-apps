import time

import nextmv
import numpy as np
import pandas as pd
from tsp import getPath, tspModel


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("maxnodes", int, 5, "Maximum number of nodes to solve the model with", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
    )

    input = nextmv.load(options=options, path=options.input)

    model = TSPModel()
    output = model.solve(input)
    nextmv.write(output, path=options.output)


class TSPModel(nextmv.Model):
    def solve(self, input: nextmv.Input) -> nextmv.Output:
        """Solves the given problem and returns the solution."""

        max_nodes = input.options.maxnodes
        start_time = time.time()
        nextmv.redirect_stdout()  # Solver chatter is logged to stderr.
        city_data = input.data
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

        statistics = nextmv.Statistics(
            run=nextmv.RunStatistics(duration=time.time() - start_time),
            result=nextmv.ResultStatistics(
                duration=tot_time,
                value=model.objective_value,
                custom={
                    "status": model.status.name,
                    "variables": model.num_variables,
                    "constraints": model.num_equations,
                    "solution_path": " -> ".join(path),
                },
            ),
        )

        return nextmv.Output(
            options=input.options,
            solution={
                "solution": sol.to_dict(),
                "total_distance": model.objective_value,
            },
            statistics=statistics,
        )


if __name__ == "__main__":
    main()
