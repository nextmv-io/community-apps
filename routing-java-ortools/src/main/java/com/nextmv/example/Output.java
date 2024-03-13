package com.nextmv.example;

import java.util.List;
import java.util.ArrayList;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;

public class Output {
  private final class Solution {
    private List<Vehicle> vehicles;
    private double value;
  }

  private final class StatisticsRun {
    private double duration;
  }

  private final class StatisticsResult {
    private double value;
    private double duration;
    private StatisticsResultCustom custom;
  }

  private final class StatisticsResultCustom {
    @SerializedName(value = "activated_vehicles")
    private int activatedVehicles;
    @SerializedName(value = "max_route_distance")
    private int maxRouteDistance;
    @SerializedName(value = "min_stops_in_vehicle")
    private int minStopsInVehicle;
    @SerializedName(value = "max_stops_in_vehicle")
    private int maxStopsInVehicle;
  }

  private final class Statistics {
    private String schema = "v1";
    private StatisticsRun run;
    private StatisticsResult result;
  }

  private final List<Solution> solutions;
  private final Statistics statistics;

  public Output(
      List<Vehicle> vehicles,
      double duration,
      double runDuration) {
    this.solutions = new ArrayList<Solution>();
    Solution solution = new Solution();
    solution.vehicles = vehicles;
    this.solutions.add(solution);
    this.statistics = new Statistics();
    this.statistics.run = new StatisticsRun();
    this.statistics.run.duration = runDuration;
    this.statistics.result = new StatisticsResult();
    this.statistics.result.duration = duration;
    
    // we are using the sum of the route distances as the value
    solution.value = vehicles.stream()
    .mapToDouble(v -> v.getDistance()).sum();
    this.statistics.result.value = solution.value;
    
    // Fill custom section.
    this.statistics.result.custom = new StatisticsResultCustom();

    // A vehicle is activated if it has at least three stops. The first and last
    // stop are the depot, so the vehicle has at least one customer stop.
    this.statistics.result.custom.activatedVehicles = (int) vehicles.stream()
        .filter(v -> v.getStops().size() > 3).count();
      
    // Find the vehicle with the maximum route distance.
    this.statistics.result.custom.maxRouteDistance = (int) vehicles.stream()
        .mapToDouble(v -> v.getDistance()).max().orElse(0);

    // Find the vehicle with the maximum number of stops.
    this.statistics.result.custom.maxStopsInVehicle = (int) vehicles.stream()
        .mapToDouble(v -> v.getStops().size()-2).max().orElse(0);

    // Find the vehicle with the minimum number of stops.
    this.statistics.result.custom.minStopsInVehicle = (int) vehicles.stream()
        .mapToDouble(v -> v.getStops().size()-2).min().orElse(0);
  }

  public static void write(String path, Output output) {
    Gson gson = new Gson();
    // Write stdout if no path is provided.
    if (path.isEmpty()) {
      System.out.println(gson.toJson(output));
      return;
    }
    // Write the path otherwise.
    try {
      java.nio.file.Files.writeString(java.nio.file.Paths.get(path), gson.toJson(output));
    } catch (java.io.IOException e) {
      System.err.println("Error writing '" + path + "': " + e.getMessage());
      System.exit(1);
    }
  }
}
