package com.nextmv.example;

import com.google.ortools.Loader;
import com.google.ortools.constraintsolver.Assignment;
import com.google.ortools.constraintsolver.FirstSolutionStrategy;
import com.google.ortools.constraintsolver.RoutingIndexManager;
import com.google.ortools.constraintsolver.RoutingModel;
import com.google.ortools.constraintsolver.RoutingSearchParameters;

import com.google.ortools.constraintsolver.main;
import com.google.protobuf.Duration;
import com.nextmv.example.Output.OutputVehicle;
import com.nextmv.example.Output.OutputVehicle.VehicleStop;

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

    // Generate all vehicle start / end indices.
    int[] startIndices = new int[input.vehicles.size()];
    int[] endIndices = new int[input.vehicles.size()];
    for (int i = 0; i < input.vehicles.size(); ++i) {
      startIndices[i] = input.stops.size() + i * 2;
      endIndices[i] = input.stops.size() + i * 2 + 1;
    }

    // Create Routing Index Manager.
    RoutingIndexManager manager = new RoutingIndexManager(
        input.stops.size() + 2 * input.vehicles.size(),
        input.vehicles.size(),
        startIndices,
        endIndices);

    // Create Routing Model.
    RoutingModel routing = new RoutingModel(manager);

    // Create and register a transit callback.
    int transitCallbackIndex;
    if (input.durationMatrix != null) {
      // If durationMatrix is provided, use it.
      transitCallbackIndex = routing.registerTransitCallback((long fromIndex, long toIndex) -> {
        int fromNode = manager.indexToNode(fromIndex);
        int toNode = manager.indexToNode(toIndex);
        return input.durationMatrix[fromNode][toNode];
      });
    } else {
      // If durationMatrix is not provided, use haversine distance.
      transitCallbackIndex = routing.registerTransitCallback((long fromIndex, long toIndex) -> {
        int fromNode = manager.indexToNode(fromIndex);
        int toNode = manager.indexToNode(toIndex);
        return (long) haversine(
            input.stops.get(fromNode).location.lat,
            input.stops.get(fromNode).location.lon,
            input.stops.get(toNode).location.lat,
            input.stops.get(toNode).location.lon);
      });
    }

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
    List<OutputVehicle> vehicles = new ArrayList<OutputVehicle>();
    for (int i = 0; i < input.vehicles.size(); ++i) {
      List<VehicleStop> stops = new ArrayList<VehicleStop>();
      long index = routing.start(i);
      long routeDuration = 0;
      while (!routing.isEnd(index)) {
        VehicleStop stop = new VehicleStop();
        stop.id = input.stops.get(manager.indexToNode(index)).id;
        stop.location = input.stops.get(manager.indexToNode(index)).location;
        stops.add(stop);
        long previousIndex = index;
        index = solution.value(routing.nextVar(index));
        routeDuration += routing.getArcCostForVehicle(previousIndex, index, i);
      }
      // Add the last stop to the route.

      OutputVehicle vehicle = new OutputVehicle();
      vehicle.id = input.vehicles.get(i).id;
      vehicles.add(vehicle);
      maxRouteDistance = Math.max(routeDuration, maxRouteDistance);
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

  /**
   * Haversine formula to calculate the distance between two points on the Earth
   * given their latitude and longitude.
   * 
   * @param lat1 latitude of the first point
   * @param lon1 longitude of the first point
   * @param lat2 latitude of the second point
   * @param lon2 longitude of the second point
   * @return the distance in kilometers between the two points
   */
  private static double haversine(double lat1, double lon1, double lat2, double lon2) {
    final double R = 6371; // Radius of the Earth in kilometers
    double latDistance = Math.toRadians(lat2 - lat1);
    double lonDistance = Math.toRadians(lon2 - lon1);
    double a = Math.sin(latDistance / 2) * Math.sin(latDistance / 2) +
        Math.cos(Math.toRadians(lat1)) * Math.cos(Math.toRadians(lat2)) *
            Math.sin(lonDistance / 2) * Math.sin(lonDistance / 2);
    double c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  }
}
