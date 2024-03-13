package com.nextmv.example;

import com.google.ortools.Loader;
import com.google.ortools.constraintsolver.Assignment;
import com.google.ortools.constraintsolver.FirstSolutionStrategy;
import com.google.ortools.constraintsolver.RoutingIndexManager;
import com.google.ortools.constraintsolver.RoutingModel;
import com.google.ortools.constraintsolver.RoutingSearchParameters;

import com.google.ortools.constraintsolver.main;
import com.google.protobuf.Duration;

import java.util.ArrayList;
import java.util.List;

public final class Main {
  public static void main(String[] args) {
    // Record start time of the program.
    long startTime = System.currentTimeMillis();
    // Parse arguments. Exit on error.
    Options options = Options.fromArguments(args);

    // Load input. Exit on error.
    Input input = Input.fromString(options.getInputPath());

    Loader.loadNativeLibraries();

    // Create Routing Index Manager.
    RoutingIndexManager manager = new RoutingIndexManager(input.distanceMatrix.length, input.vehicleNumber,
        input.depot);

    // Create Routing Model.
    RoutingModel routing = new RoutingModel(manager);

    // Create and register a transit callback.
    final int transitCallbackIndex = routing.registerTransitCallback((long fromIndex, long toIndex) -> {
      // Convert from routing variable Index to user NodeIndex.
      int fromNode = manager.indexToNode(fromIndex);
      int toNode = manager.indexToNode(toIndex);
      return input.distanceMatrix[fromNode][toNode];
    });

    // Define cost of each arc.
    routing.setArcCostEvaluatorOfAllVehicles(transitCallbackIndex);

    // Set the duration of the search.
    Duration duration = Duration.newBuilder().setSeconds(options.getDuration()).build();

    // Setting first solution heuristic.
    RoutingSearchParameters searchParameters = main.defaultRoutingSearchParameters()
        .toBuilder()
        .setFirstSolutionStrategy(FirstSolutionStrategy.Value.PATH_CHEAPEST_ARC)
        .setTimeLimit(duration)
        .build();

    // Solve the problem.
    // Record solve start time
    long solveStartTime = System.currentTimeMillis();
    Assignment solution = routing.solveWithParameters(searchParameters);

    Output output = getOutput(startTime, input, routing, manager, solution, solveStartTime);

    // Write output. Exit on error.
    Output.write(options.getOutputPath(), output);
  }

  static Output getOutput(
      long startTime,
      Input input,
      RoutingModel routing,
      RoutingIndexManager manager,
      Assignment solution, long solveStartTime) {
    long maxRouteDistance = 0;
    List<Vehicle> vehicles = new ArrayList<Vehicle>();
    for (int i = 0; i < input.vehicleNumber; ++i) {
      List<Integer> stops = new ArrayList<Integer>();
      long index = routing.start(i);
      long routeDistance = 0;
      while (!routing.isEnd(index)) {
        stops.add(manager.indexToNode(index));
        long previousIndex = index;
        index = solution.value(routing.nextVar(index));
        routeDistance += routing.getArcCostForVehicle(previousIndex, index, i);
      }
      stops.add(manager.indexToNode(index));
      Vehicle vehicle = new Vehicle(i, routeDistance, stops);
      vehicles.add(vehicle);
      maxRouteDistance = Math.max(routeDistance, maxRouteDistance);
    }

    // Compute solve duration.
    long endTime = System.currentTimeMillis();
    double duration = endTime - solveStartTime;
    // Convert duration to seconds.
    duration = duration / 1000.0;

    // Compute total duration.
    endTime = System.currentTimeMillis();
    double runDuration = endTime - startTime;
    // Convert duration to seconds.
    runDuration = runDuration / 1000.0;

    // Create output.
    return new Output(
        vehicles,
        duration,
        runDuration);
  }
}
