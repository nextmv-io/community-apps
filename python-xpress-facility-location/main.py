import time

import nextmv
from visuals import draw_sol
import numpy as np
import json

try:
    import xpress as xp
except ImportError as exc:
    raise ImportError("is xpress available for your OS and ARCH and installed?") from exc

import sys
import os
# Redirect stdout to stderr to suppress license warnings
original_stdout = sys.stdout
sys.stdout = sys.stderr

# Status of the solver after optimizing.
STATUS = {
    xp.SolStatus.FEASIBLE: "suboptimal",
    xp.SolStatus.INFEASIBLE: "infeasible",
    xp.SolStatus.OPTIMAL: "optimal",
    xp.SolStatus.UNBOUNDED: "unbounded",
}


def main() -> None:
    """Entry point for the program."""

    options = nextmv.Options(
        nextmv.Option("input", str, "", "Path to input file. Default is stdin.", False),
        nextmv.Option("output", str, "", "Path to output file. Default is stdout.", False),
        nextmv.Option("duration", int, 30, "Max runtime duration (in seconds).", False),
    )

    input = nextmv.load(options=options, path=options.input)

    nextmv.log("Solving facility location problem:")
    nextmv.log(f"  - schools: {input.data.get('num_schools', [])}")
    nextmv.log(f"  - sites: {input.data.get('num_sites', 0)}")
    nextmv.log(f"  - parks: {input.data.get('num_parks', 0)}")

    SCHOOLS = range(input.data.get('num_schools'))  # set of schools
    SITES = range(input.data.get('num_sites'))      # set of candidate sites

    coord_schools = 10 * np.random.random((input.data.get('num_schools'), 2))  # x-y coordinates between 0 and 10 (in km)
    coord_sites   = 10 * np.random.random((input.data.get('num_sites'), 2))

    # Create a dictionary with the distances between schools and candidate sites
    dist = {(i,j): np.linalg.norm([coord_schools[i] - coord_sites[j]]) for i in SCHOOLS for j in SITES}

    prob = xp.problem()

    serves = prob.addVariables(SCHOOLS, SITES, vartype=xp.binary)
    build = prob.addVariables(SITES, vartype=xp.binary)

    # Objective function and constraints
    prob.setObjective(xp.Sum(dist[i,j] * serves[i,j] for i in SCHOOLS for j in SITES))

    # Every school must be served by one park
    prob.addConstraint(xp.Sum(serves[i,j] for j in SITES) == 1 for i in SCHOOLS)

    # Exactly n parks are built:
    prob.addConstraint(xp.Sum(build[j] for j in SITES) == input.data.get('num_parks'))

    # Only parks that are built can serve schools
    prob.addConstraint(xp.Sum(serves[i,j] for i in SCHOOLS) <= input.data.get('num_schools') * build[j] for j in SITES)

    prob.optimize()

    prob.write("problem.lp")
    solution = json.dumps(prob.getSolution())
    value = prob.attributes.objval


    input.options.provider = "xpress"

    input_charts = draw_sol(n=input.data.get('num_schools'),m=input.data.get('num_sites'), label="Input Chart", coord_schools=coord_schools, coord_sites=coord_sites, SCHOOLS=SCHOOLS, SITES=SITES)
    output_charts = draw_sol(input.data.get('num_schools'),input.data.get('num_sites'),prob,serves,build, "Output Chart", coord_schools=coord_schools, coord_sites=coord_sites, SCHOOLS=SCHOOLS, SITES=SITES)

    sys.stdout = original_stdout

    
    return nextmv.Output(
           solution={"solution": solution},
           statistics={"result": {"value": value}, "schema": "v1"},
           assets=[input_charts, output_charts]
       )


if __name__ == "__main__":
    main()
