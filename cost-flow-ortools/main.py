"""
Template to solve a cost flow problem with Google OR-Tools.
"""

import argparse
import json
import sys
import time
from typing import Any

from ortools.graph.python import min_cost_flow

STATUS = {
    min_cost_flow.SimpleMinCostFlow.OPTIMAL: "optimal",
    min_cost_flow.SimpleMinCostFlow.BAD_COST_RANGE: "bad cost range",
    min_cost_flow.SimpleMinCostFlow.BAD_RESULT: "bad result",
    min_cost_flow.SimpleMinCostFlow.FEASIBLE: "feasible",
    min_cost_flow.SimpleMinCostFlow.INFEASIBLE: "infeasible",
    min_cost_flow.SimpleMinCostFlow.NOT_SOLVED: "not solved",
    min_cost_flow.SimpleMinCostFlow.UNBALANCED: "unbalanced"
}

def main() -> None:
    """Entry point for the template."""

    parser = argparse.ArgumentParser(description="Solve cost-flow with OR-Tools.")
    parser.add_argument(
        "-input",
        default="",
        help="Path to input file. Default is stdin.",
    )
    parser.add_argument(
        "-output",
        default="",
        help="Path to output file. Default is stdout.",
    )
    parser.add_argument(
        "-penalty",
        default=3000,
        help="A penalty added to the edges from dummy source to projects. Default is 3000.",
    )
    args = parser.parse_args()

    # Read input data, solve the problem and write the solution.
    input_data = read_input(args.input)
    log("Best value flow for project to worker assignment:")
    log(f"  - projects: {len(input_data.get('projects', []))}")
    log(f"  - workers: {len(input_data.get('workers', []))}")
    log(f"  - penalty: {args.penalty}")
    solution = solve(input_data, float(args.penalty))
    write_output(args.output, solution)


def solve(input_data: dict[str, Any], penalty: float) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    err = validateSkills(input_data)
    if err:
        return err

    total_available_time = 0
    total_required_time = 0
    project_to_open_time_units = {}
    project_to_value = {}

    for worker in input_data["workers"]:
        total_available_time += worker["available_time"]

    for project in input_data["projects"]:
        total_required_time += project["required_time"]
        project_to_open_time_units[project["id"]] = project["required_time"]
        project_to_value[project["id"]] = project["value"]

    start_nodes = []
    end_nodes = []
    capacities = []
    unit_costs = []
    supply = [total_available_time, -1 * total_required_time]

    index_source = 0
    index_sink = 1
    index_dummy_source = 2
    index_dummy_sink = 3
    structure_node_count = 4

    # Do we need dummy flows for excess supply or unmet demands?
    # dummy source
    if total_available_time < total_required_time:
        supply.append(total_required_time - total_available_time)
    else:
        supply.append(0)

    # dummy sink
    if total_required_time < total_available_time:
        supply.append(total_required_time - total_available_time)
    else:
        supply.append(0)

    # create edges: source to workers
    for i in range(0, len(input_data["workers"])):
        start_nodes.append(index_source)
        end_nodes.append(structure_node_count + i)
        capacities.append(input_data["workers"][i]["available_time"])
        unit_costs.append(0)
        supply.append(0)

    # create edges: worker to project, consider skills
    for i in range(0, len(input_data["workers"])):
        worker = input_data["workers"][i]
        for j in range(0, len(input_data["projects"])):
            project = input_data["projects"][j]
            is_contained = all(element in worker["skills"] for element in project["required_skills"])
            if is_contained:
                start_nodes.append(structure_node_count + i)
                end_nodes.append(structure_node_count + len(input_data["workers"]) + j)
                capacities.append(worker["available_time"])  # assignment of a worker to a project
                unit_costs.append(-1 * round(project["value"] / project["required_time"], 2))

    # create edges: project to sink
    for i in range(0, len(input_data["projects"])):
        start_nodes.append(structure_node_count + len(input_data["workers"]) + i)
        end_nodes.append(index_sink)
        capacities.append(input_data["projects"][i]["required_time"])
        unit_costs.append(0)
        supply.append(0)

    # create edges: workers to dummy sink
    workers_to_dummy_sink_indices = []
    for i in range(0, len(input_data["workers"])):
        workers_to_dummy_sink_indices.append(len(start_nodes))
        start_nodes.append(structure_node_count + i)
        end_nodes.append(index_dummy_sink)
        capacities.append(input_data["workers"][i]["available_time"])
        unit_costs.append(0)

    # create edges: dummy source to projects
    dummy_source_to_project_indices = []
    for i in range(0, len(input_data["projects"])):
        dummy_source_to_project_indices.append(len(start_nodes))
        start_nodes.append(index_dummy_source)
        end_nodes.append(structure_node_count + len(input_data["workers"]) + i)
        if total_required_time - total_available_time < 0:
            capacities.append(0)
        else:
            capacities.append(total_required_time - total_available_time)
        unit_costs.append(penalty)

    solver = min_cost_flow.SimpleMinCostFlow()

    all_arcs = solver.add_arcs_with_capacity_and_unit_cost(
        start_nodes, end_nodes, capacities, unit_costs
    )
    solver.set_nodes_supplies(range(0, len(supply)), supply)

    start = time.process_time()
    status = solver.solve()
    end = time.process_time()

    wall_time = end - start

    solution_flows = solver.flows(all_arcs)
    costs = solution_flows * unit_costs * -1

    # Creates the statistics.
    # Compute the number of time units required from the dummy source
    dummy_source_units = 0
    for idx in dummy_source_to_project_indices:
        dummy_source_units += int(solution_flows[idx])
    # Compute the number of time units that are in excess
    dummy_sink_units = 0
    for idx in workers_to_dummy_sink_indices:
        dummy_sink_units += int(solution_flows[idx])
    statistics = {
        "result": {
            "custom": {
                "number_of_edges": solver.num_arcs(),
                "number_of_nodes": solver.num_nodes(),
                "number_of_workers": len(input_data["workers"]),
                "number_of_projects": len(input_data["projects"]),
                "available_time_units": total_available_time,
                "required_time_units": total_required_time,
                "excess_time_units": dummy_sink_units,
                "unmet_time_units": dummy_source_units,
                "number_of_fulfilled_projects": 0,
                "number_of_unfulfilled_projects": 0
            },
            "duration": wall_time,
            "value": solver.optimal_cost(),
        },
        "run": {
            "duration": wall_time,
        },
        "schema": "v1",
    }

    # create the solution information
    # flows: just lists all edges and their flows
    # assignments: which worker is assigned to which project
    # value: what is the actual value of projects that can be
    # fulfilled (only considers projects that don't need the dummy source)
    solution = {"flows": [], "assignments": [], "status": STATUS.get(status, "unknown")}
    if status == min_cost_flow.SimpleMinCostFlow.OPTIMAL or status == min_cost_flow.SimpleMinCostFlow.FEASIBLE:
        total_value = 0
        fulfilled_projects = 0
        for i in range(0, len(solution_flows)):
            solution["flows"].append(
                {
                    "from": start_nodes[i],
                    "to": end_nodes[i],
                    "flow": int(solution_flows[i]),
                    "capacity": int(capacities[i]),
                    "value": int(costs[i])
                }
            )

            # look at the flows between workers and projects to get the assignments
            if solution_flows[i] > 0 and start_nodes[i] != 0 \
                    and end_nodes[i] != 1 and start_nodes[i] != 2 and end_nodes[i] != 3:
                project_id = input_data["projects"][end_nodes[i] - 4 - len(input_data["workers"])]["id"]
                solution["assignments"].append(
                    {
                        "project": project_id,
                        "worker": input_data["workers"][start_nodes[i] - 4]["id"],
                        "value": input_data["projects"][end_nodes[i] - 4 - len(input_data["workers"])]["value"],
                        "time_units": int(solution_flows[i]),
                    }
                )

                # Compute the number of projects that can be fulfilled with workers
                project_to_open_time_units[project_id] -= int(solution_flows[i])

        for pid in project_to_open_time_units:
            if project_to_open_time_units[pid] == 0:
                total_value += project_to_value[pid]
                fulfilled_projects += 1

        solution["total_value_of_fulfilled_projects"] = total_value
        statistics["result"]["custom"]["number_of_fulfilled_projects"] = fulfilled_projects
        statistics["result"]["custom"]["number_of_unfilled_projects"] = len(input_data["projects"]) - fulfilled_projects

    log(f"  - status: {STATUS.get(status, 'unknown')}")
    log(f"  - value: {statistics['result']['value']}")
    log(f"  - total value of fulfilled projects: {solution['total_value_of_fulfilled_projects']}")
    log(f"  - number of fulfilled projects: {statistics['result']['custom']['number_of_fulfilled_projects']}")
    log(f"  - number of unfulfilled projects: {statistics['result']['custom']['number_of_unfilled_projects']}")

    return {
        "solution": solution,
        "statistics": statistics,
    }

def validateSkills(input_data: dict[str, Any]) -> Any:
    """Check that each project skill and each worker skill have a skill pair."""
    for project in input_data["projects"]:
        for skill in project["required_skills"]:
            if not any(skill in worker["skills"] for worker in input_data["workers"]):
                return errorStatusOutput("input_skill_error")
    for worker in input_data["workers"]:
        for skill in worker["skills"]:
            if not any(skill in project["required_skills"] for project in input_data["projects"]):
                return errorStatusOutput("input_skill_error")
    return None

def errorStatusOutput(status: str) -> dict[str, Any]:
    """Returns an error output with a given status."""

    return {
            "solution": {
                "flows": [],
                "assignments": [],
                "status": f"{status}",
            },
            "statistics": {
                "result": {
                    "custom": {
                        "number_of_edges": 0,
                        "number_of_nodes": 0,
                        "number_of_workers": 0,
                        "number_of_projects": 0,
                        "available_time_units": 0,
                        "required_time_units": 0,
                        "excess_time_units": 0,
                        "unmet_time_units": 0,
                        "number_of_fulfilled_projects": 0,
                        "number_of_unfulfilled_projects": 0
                    },
                    "duration": 0,
                    "value": 0,
                },
                "run": {
                    "duration": 0,
                },
                "schema": "v1",
            }
        }


def log(message: str) -> None:
    """Logs a message. We need to use stderr since stdout is used for the
    solution."""

    print(message, file=sys.stderr)


def read_input(input_path) -> dict[str, Any]:
    """Reads the input from stdin or a given input file."""

    input_file = {}
    if input_path:
        with open(input_path, encoding="utf-8") as file:
            input_file = json.load(file)
    else:
        input_file = json.load(sys.stdin)

    return input_file


def write_output(output_path, output) -> None:
    """Writes the output to stdout or a given output file."""

    content = json.dumps(output, indent=2)
    if output_path:
        with open(output_path, "w", encoding="utf-8") as file:
            file.write(content + "\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
