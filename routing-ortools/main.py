"""
Adapted example of the vehicle routing problem with Google OR-Tools.
"""

import argparse
import json
import sys
import time
from typing import Any

from ortools.constraint_solver import pywrapcp, routing_enums_pb2


def main():
    """Entry point for the template."""
    parser = argparse.ArgumentParser(description="Solve a routing problem with OR-Tools.")
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
        "-duration",
        default=30,
        help="Max runtime duration (in seconds). Default is 30.",
        type=int,
    )
    args = parser.parse_args()

    # Read input data, solve the problem and write the solution.
    input_data = read_input(args.input)
    log("Solving routing problem:")
    log(f"  - num_vehicles: {input_data.get('num_vehicles', 0)}")
    log(f"  - stops: {len(input_data.get('distance_matrix', []))-1}")
    log(f"  - max duration: {args.duration} seconds")
    solution = solve(input_data, args.duration)
    write_output(args.output, solution)


def solve(input_data: dict[str, Any], duration: int) -> dict[str, Any]:
    """Solves the given problem and returns the solution."""

    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(input_data["distance_matrix"]),
        input_data["num_vehicles"],
        input_data["depot"],
    )

    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return input_data["distance_matrix"][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_parameters.time_limit.FromSeconds(duration)

    # Solve the problem.
    start_time = time.time()
    solution = routing.SolveWithParameters(search_parameters)
    end_time = time.time()

    if solution is not None:
        # Determine the routes.
        routes = []
        max_route_distance = 0
        max_stops_in_vehicle = 0
        min_stops_in_vehicle = len(input_data["distance_matrix"])
        activated_vehicles = 0
        for vehicle_id in range(input_data["num_vehicles"]):
            index = routing.Start(vehicle_id)
            route_distance = 0
            stops = []
            while not routing.IsEnd(index):
                stops.append(manager.IndexToNode(index))
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(
                    previous_index,
                    index,
                    vehicle_id,
                )
            stops.append(manager.IndexToNode(index))
            route = {
                "vehicle": vehicle_id,
                "distance": route_distance,
                "stops": stops,
            }
            routes.append(route)
            max_route_distance = max(route_distance, max_route_distance)
            activated_vehicles += 1
            max_stops_in_vehicle = max(max_stops_in_vehicle, len(stops) - 2)
            min_stops_in_vehicle = min(min_stops_in_vehicle, len(stops) - 2)

        # Creates the statistics.
        statistics = {
            "result": {
                "custom": {
                    "activated_vehicles": activated_vehicles,
                    "max_route_distance": max_route_distance,
                    "max_stops_in_vehicle": max_stops_in_vehicle,
                    "min_stops_in_vehicle": min_stops_in_vehicle,
                },
                "duration": end_time - start_time,
                "value": solution.ObjectiveValue(),
            },
            "run": {
                "duration": end_time - start_time,
            },
            "schema": "v1",
        }
    else:
        routes = []
        statistics = {
            "result": {
                "custom": {},
                "duration": end_time - start_time,
                "value": None,
            },
            "run": {
                "duration": end_time - start_time,
            },
            "schema": "v1",
        }

    return {
        "solutions": [{"vehicles": routes}],
        "statistics": statistics,
    }


def log(message: str) -> None:
    """Logs a message. We need to use stderr since stdout is used for the solution."""

    print(message, file=sys.stderr)


def read_input(input_path) -> dict[str, Any]:
    """Reads the input from stdin or a given input file."""
    input_file = {}
    if input_path:
        with open(input_path) as file:
            input_file = json.load(file)
    else:
        input_file = json.load(sys.stdin)

    return input_file


def write_output(output_path, output) -> None:
    """Writes the output to stdout or a given output file."""
    content = json.dumps(output, indent=2)
    if output_path:
        with open(output_path, "w") as file:
            file.write(content + "\n")
    else:
        print(content)


if __name__ == "__main__":
    main()
