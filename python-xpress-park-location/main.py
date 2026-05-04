import json
from typing import Any

import nextmv
import numpy as np
import xpress as xp
from visuals import draw_sol

# Status of the solver after optimizing.
STATUS = {
    xp.SolStatus.FEASIBLE: "suboptimal",
    xp.SolStatus.INFEASIBLE: "infeasible",
    xp.SolStatus.OPTIMAL: "optimal",
    xp.SolStatus.UNBOUNDED: "unbounded",
}


def main() -> None:
    """Entry point for the program."""

    loaded_input = nextmv.load()
    options = loaded_input.options

    valid = {"average_distance", "total_distance", "max_distance"}
    if options.objective not in valid:
        raise ValueError(f"Invalid objective. Must be in set {valid}.")

    nextmv.log("Solving park location problem:")
    nextmv.log(f"  - objective: {options.objective}")
    nextmv.log(f"  - parks_override: {options.parks_override}")
    nextmv.log(f"  - schools: {loaded_input.data.get('num_schools')}")
    nextmv.log(f"  - sites: {loaded_input.data.get('num_sites')}")
    nextmv.log(f"  - parks: {loaded_input.data.get('num_parks')}")

    solution, metrics, assets = solve(loaded_input, options)
    nextmv.write(solution=solution, metrics=metrics, options=options, assets=assets)


def solve(
    loaded_input: nextmv.Input, options: nextmv.Options
) -> tuple[dict[str, Any], dict[str, Any], list[nextmv.Asset]]:
    """Solves the given problem and returns the solution, metrics, and assets."""

    np.random.seed(loaded_input.data.get("seed"))

    SCHOOLS = range(loaded_input.data.get("num_schools"))  # set of schools
    SITES = range(loaded_input.data.get("num_sites"))  # set of candidate sites
    num_parks = loaded_input.data.get("num_parks")
    if options.parks_override is not None:
        num_parks = options.parks_override

    # x-y coordinates between 0 and 10 (in km)
    coord_schools = 10 * np.random.random((loaded_input.data.get("num_schools"), 2))
    coord_sites = 10 * np.random.random((loaded_input.data.get("num_sites"), 2))

    # Create a dictionary with the distances between schools and candidate sites
    dist = {(i, j): np.linalg.norm([coord_schools[i] - coord_sites[j]]) for i in SCHOOLS for j in SITES}

    nextmv.redirect_stdout()  # Redirect solver output to stderr
    prob = xp.problem()

    serves = prob.addVariables(SCHOOLS, SITES, vartype=xp.binary)
    build = prob.addVariables(SITES, vartype=xp.binary)

    # Objective function and constraints
    if options.objective == "average_distance":
        prob.setObjective(
            xp.Sum(dist[i, j] * serves[i, j] for i in SCHOOLS for j in SITES) / loaded_input.data.get("num_schools")
        )
    elif options.objective == "total_distance":
        prob.setObjective(xp.Sum(dist[i, j] * serves[i, j] for i in SCHOOLS for j in SITES))
    elif options.objective == "max_distance":
        z = prob.addVariable()  # add auxiliary variable to the problem
        prob.addConstraint(z >= xp.Sum(dist[i, j] * serves[i, j] for j in SITES) for i in SCHOOLS)
        prob.setObjective(z)  # replaces the old objective function

    # Every school must be served by one park
    prob.addConstraint(xp.Sum(serves[i, j] for j in SITES) == 1 for i in SCHOOLS)

    # Exactly n parks are built
    prob.addConstraint(xp.Sum(build[j] for j in SITES) == num_parks)

    # Only parks that are built can serve schools
    prob.addConstraint(
        xp.Sum(serves[i, j] for i in SCHOOLS) <= loaded_input.data.get("num_schools") * build[j] for j in SITES
    )

    _, status = prob.optimize()

    prob.write("problem.lp")
    solution_data = json.dumps(prob.getSolution())
    value = prob.attributes.objval

    input_charts = draw_sol(
        n=loaded_input.data.get("num_schools"),
        m=loaded_input.data.get("num_sites"),
        label="Input Chart",
        coord_schools=coord_schools,
        coord_sites=coord_sites,
        SCHOOLS=SCHOOLS,
        SITES=SITES,
        tab_order=1,
    )
    output_charts = draw_sol(
        loaded_input.data.get("num_schools"),
        loaded_input.data.get("num_sites"),
        prob,
        serves,
        build,
        label="Output Chart",
        coord_schools=coord_schools,
        coord_sites=coord_sites,
        SCHOOLS=SCHOOLS,
        SITES=SITES,
        tab_order=2,
    )

    sol = prob.getSolution(serves)
    average_distance = sum(dist[i, j] * sol[i, j] for i in SCHOOLS for j in SITES) / loaded_input.data.get(
        "num_schools"
    )
    total_distance = sum(dist[i, j] * sol[i, j] for i in SCHOOLS for j in SITES)
    max_distance = max(dist[i, j] for i in SCHOOLS for j in SITES if sol[i, j] > 0.5)

    nextmv.log(f"average_distance: {average_distance}")
    nextmv.log(f"total_distance: {total_distance}")
    nextmv.log(f"max_distance: {max_distance}")

    solution = {"solution": solution_data}
    metrics = {
        "result_value": value,
        "average_distance": average_distance,
        "total_distance": total_distance,
        "max_distance": max_distance,
        "status": STATUS.get(status, "unknown"),
        "variables": prob.getAttrib("cols"),
        "constraints": prob.getAttrib("rows"),
    }
    assets = [input_charts, output_charts]

    return solution, metrics, assets


if __name__ == "__main__":
    main()
