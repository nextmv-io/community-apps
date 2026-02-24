import json

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

    manifest = nextmv.Manifest.from_yaml(".")
    options = manifest.extract_options()

    input = nextmv.load(options=options, path=options.input)
    valid = {"average_distance", "total_distance", "max_distance"}
    if options.objective not in valid:
        raise ValueError(f"Invalid objective. Must be in set {valid}.")

    nextmv.log("Solving facility location problem:")
    nextmv.log(f"  - objective: {options.objective}")
    nextmv.log(f"  - parks_override: {options.parks_override}")
    nextmv.log(f"  - schools: {input.data.get('num_schools')}")
    nextmv.log(f"  - sites: {input.data.get('num_sites')}")
    nextmv.log(f"  - parks: {input.data.get('num_parks')}")

    np.random.seed(input.data.get("seed"))

    SCHOOLS = range(input.data.get("num_schools"))  # set of schools
    SITES = range(input.data.get("num_sites"))  # set of candidate sites
    num_parks = input.data.get("num_parks")
    if options.parks_override is not None:
        num_parks = options.parks_override

    # x-y coordinates between 0 and 10 (in km)
    coord_schools = 10 * np.random.random((input.data.get("num_schools"), 2))
    coord_sites = 10 * np.random.random((input.data.get("num_sites"), 2))

    # Create a dictionary with the distances between schools and candidate sites
    dist = {(i, j): np.linalg.norm([coord_schools[i] - coord_sites[j]]) for i in SCHOOLS for j in SITES}

    nextmv.redirect_stdout()  # Redirect solver output to stderr
    prob = xp.problem()

    serves = prob.addVariables(SCHOOLS, SITES, vartype=xp.binary)
    build = prob.addVariables(SITES, vartype=xp.binary)

    # Objective function and constraints
    if options.objective == "average_distance":
        prob.setObjective(
            xp.Sum(dist[i, j] * serves[i, j] for i in SCHOOLS for j in SITES) / input.data.get("num_schools")
        )
    elif options.objective == "total_distance":
        prob.setObjective(xp.Sum(dist[i, j] * serves[i, j] for i in SCHOOLS for j in SITES))
    elif options.objective == "max_distance":
        z = prob.addVariable()  # add auxiliary variable to the problem
        prob.addConstraint(z >= xp.Sum(dist[i, j] * serves[i, j] for j in SITES) for i in SCHOOLS)
        prob.setObjective(z)  # replaces the old objective function

    # Every school must be served by one park
    prob.addConstraint(xp.Sum(serves[i, j] for j in SITES) == 1 for i in SCHOOLS)

    # Exactly n parks are built:
    prob.addConstraint(xp.Sum(build[j] for j in SITES) == num_parks)

    # Only parks that are built can serve schools
    prob.addConstraint(xp.Sum(serves[i, j] for i in SCHOOLS) <= input.data.get("num_schools") * build[j] for j in SITES)

    prob.optimize()

    prob.write("problem.lp")
    solution = json.dumps(prob.getSolution())
    value = prob.attributes.objval

    input.options.provider = "xpress"

    input_charts = draw_sol(
        n=input.data.get("num_schools"),
        m=input.data.get("num_sites"),
        label="Input Chart",
        coord_schools=coord_schools,
        coord_sites=coord_sites,
        SCHOOLS=SCHOOLS,
        SITES=SITES,
        tab_order=1,
    )
    output_charts = draw_sol(
        input.data.get("num_schools"),
        input.data.get("num_sites"),
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
    average_distance = sum(dist[i, j] * sol[i, j] for i in SCHOOLS for j in SITES) / input.data.get("num_schools")
    total_distance = sum(dist[i, j] * sol[i, j] for i in SCHOOLS for j in SITES)
    max_distance = max(dist[i, j] for i in SCHOOLS for j in SITES if sol[i, j] > 0.5)

    nextmv.log(f"average_distance: {average_distance}")
    nextmv.log(f"total_distance: {total_distance}")
    nextmv.log(f"max_distance: {max_distance}")

    output = nextmv.Output(
        solution={"solution": solution},
        assets=[input_charts, output_charts],
        metrics={
            "result_value": value,
            "average_distance": average_distance,
            "total_distance": total_distance,
            "max_distance": max_distance,
        },
    )

    nextmv.write(output, path=options.output)


if __name__ == "__main__":
    main()
