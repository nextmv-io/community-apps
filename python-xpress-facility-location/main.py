import time
from typing import Any

import nextmv
import xpress as xp

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

    nextmv.log("Solving stochastic facility location problem:")
    nextmv.log(f"  - facilities: {len(loaded_input.data['FACILITIES'])}")
    nextmv.log(f"  - customers: {len(loaded_input.data['CUSTOMERS'])}")
    nextmv.log(f"  - scenarios: {len(loaded_input.data['SCENARIOS'])}")

    solution, metrics = solve(loaded_input)
    nextmv.write(solution=solution, metrics=metrics, options=options)


def solve(input: nextmv.Input) -> tuple[dict[str, Any], dict[str, Any]]:
    """Solves the given problem and returns the solution and metrics."""

    start_time = time.time()
    nextmv.redirect_stdout()  # Solver chatter is logged to stderr.

    # Extract data and options from input.
    data = input.data
    options = input.options

    facilities = data["FACILITIES"]
    customers = data["CUSTOMERS"]
    scenarios = data["SCENARIOS"]
    scenario_prob = data["prob"]

    # Build dictionaries from data.
    fixed_cost = {row["City"]: row["FixedCost"] for row in data["fixed_cost"]}
    facility_capacity = {row["City"]: row["Capacity"] for row in data["facility_capacity"]}
    variable_cost = {(row["Facility"], row["Customer"]): row["Distance"] for row in data["variable_cost"]}
    customer_demand = {(row["City"], s): row[s] for row in data["customer_demand"] for s in scenarios}

    # Benders decomposition parameters.
    epsilon = options.epsilon
    max_iterations = options.max_iterations

    # Storage for cuts: (type, scenario, customer_prices, facility_prices).
    cuts = []

    # Initialize master solution.
    master_facility_open = dict.fromkeys(facilities, 0)
    master_sub_cost = dict.fromkeys(scenarios, 0)

    total_solve_time = 0.0
    iteration = 0
    converged = False

    for iteration in range(1, max_iterations + 1):
        nextmv.log(f"\nITERATION {iteration}")
        no_violation = dict.fromkeys(scenarios, False)

        # Solve subproblem for each scenario.
        for s in scenarios:
            sub_result = _solve_subproblem(
                facilities, customers, s, variable_cost, customer_demand, facility_capacity, master_facility_open
            )
            total_solve_time += sub_result["solve_time"]

            if sub_result["status"] == "infeasible":
                cuts.append(("feas", s, sub_result["customer_prices"], sub_result["facility_prices"]))
                nextmv.log(f"{iteration}: Feasibility cut added for scenario {s}")
            elif sub_result["objective"] > master_sub_cost[s] + epsilon:
                cuts.append(("opt", s, sub_result["customer_prices"], sub_result["facility_prices"]))
                nextmv.log(f"{iteration}: Optimality cut added for scenario {s}")
            else:
                no_violation[s] = True
                nextmv.log(f"{iteration}: No cut needed for scenario {s}")

        # Check for convergence.
        if all(no_violation.values()):
            nextmv.log(f"\nOPTIMAL SOLUTION FOUND after {iteration} iterations")
            converged = True
            break

        # Solve master problem.
        nextmv.log("\nSOLVING MASTER PROBLEM")
        master_result = _solve_master(
            facilities,
            customers,
            scenarios,
            fixed_cost,
            facility_capacity,
            customer_demand,
            scenario_prob,
            cuts,
            options.duration,
        )
        total_solve_time += master_result["solve_time"]
        master_facility_open = master_result["facility_open"]
        master_sub_cost = master_result["sub_cost"]

    # Calculate final total cost.
    total_fixed_cost = sum(fixed_cost[f] * master_facility_open[f] for f in facilities)
    total_variable_cost = sum(scenario_prob[s] * master_sub_cost[s] for s in scenarios)
    total_cost = total_fixed_cost + total_variable_cost

    # Determine which facilities are open.
    open_facilities = [f for f in facilities if master_facility_open[f] > 0.5]

    solution = {
        "facilities": open_facilities,
        "total_cost": total_cost,
        "fixed_cost": total_fixed_cost,
        "variable_cost": total_variable_cost,
    }
    metrics = {
        "duration": time.time() - start_time,
        "solve_duration": total_solve_time,
        "value": total_cost,
        "status": "optimal" if converged else "limit",
        "iterations": iteration,
    }

    return solution, metrics


def _solve_subproblem(
    facilities,
    customers,
    scenario,
    variable_cost,
    customer_demand,
    facility_capacity,
    facility_open,
):
    """Solve the subproblem for a given scenario and facility configuration."""

    problem = xp.problem()
    problem.controls.outputlog = 0

    # Variables: production[i,j] = amount produced at facility i for customer j.
    production = {(i, j): problem.addVariable(lb=0, name=f"prod_{i}_{j}") for i in facilities for j in customers}

    # Objective: minimize variable cost.
    problem.setObjective(
        xp.Sum(variable_cost[i, j] * production[i, j] for i in facilities for j in customers),
        sense=xp.minimize,
    )

    # Constraints: satisfy customer demand.
    for j in customers:
        problem.addConstraint(xp.Sum(production[i, j] for i in facilities) >= customer_demand[j, scenario])

    # Constraints: facility capacity limits.
    for i in facilities:
        problem.addConstraint(xp.Sum(production[i, j] for j in customers) <= facility_capacity[i] * facility_open[i])

    problem.lpOptimize()

    result = {
        "solve_time": problem.attributes.time,
        "customer_prices": {},
        "facility_prices": {},
    }

    if problem.attributes.lpstatus == xp.LPStatus.INFEAS:
        result["status"] = "infeasible"
        result["objective"] = float("inf")
        # Use zero duals for infeasible case (cut will force opening facilities).
        for j in customers:
            result["customer_prices"][j] = 0.0
        for i in facilities:
            result["facility_prices"][i] = 0.0
    else:
        result["status"] = "optimal"
        result["objective"] = problem.attributes.objval
        # Get dual values.
        duals = problem.getDuals()
        for idx, j in enumerate(customers):
            result["customer_prices"][j] = max(duals[idx], 0)
        for idx, i in enumerate(facilities):
            result["facility_prices"][i] = min(duals[len(customers) + idx], 0)

    return result


def _solve_master(
    facilities,
    customers,
    scenarios,
    fixed_cost,
    facility_capacity,
    customer_demand,
    scenario_prob,
    cuts,
    duration,
):
    """Solve the master problem with accumulated Benders cuts."""

    problem = xp.problem()
    problem.controls.outputlog = 0
    problem.controls.maxtime = duration

    # Variables.
    facility_open = {i: problem.addVariable(vartype=xp.binary, name=f"open_{i}") for i in facilities}
    sub_cost = {s: problem.addVariable(lb=0, name=f"sub_cost_{s}") for s in scenarios}

    # Objective: minimize total cost.
    problem.setObjective(
        xp.Sum(fixed_cost[i] * facility_open[i] for i in facilities)
        + xp.Sum(scenario_prob[s] * sub_cost[s] for s in scenarios),
        sense=xp.minimize,
    )

    # Constraint: sufficient production capacity.
    max_demand = max(sum(customer_demand[j, s] for j in customers) for s in scenarios)
    problem.addConstraint(xp.Sum(facility_capacity[i] * facility_open[i] for i in facilities) >= max_demand)

    # Add Benders cuts.
    for cut_type, s, customer_prices, facility_prices in cuts:
        lhs = sum(customer_prices[j] * customer_demand[j, s] for j in customers) + xp.Sum(
            facility_prices[i] * facility_capacity[i] * facility_open[i] for i in facilities
        )
        if cut_type == "opt":
            problem.addConstraint(lhs <= sub_cost[s])
        elif cut_type == "feas":
            problem.addConstraint(lhs <= 0)

    problem.optimize()

    return {
        "solve_time": problem.attributes.time,
        "facility_open": {i: problem.getSolution(facility_open[i]) for i in facilities},
        "sub_cost": {s: problem.getSolution(sub_cost[s]) for s in scenarios},
        "objective": problem.attributes.objval,
    }


if __name__ == "__main__":
    main()
