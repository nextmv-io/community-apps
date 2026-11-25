package com.nextmv.example;

import java.util.List;
import java.util.ArrayList;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;
import com.nextmv.example.Input.Location;

/**
 * Output represents the solution itself and other additional information
 * about the run such as statistics.
 * The implementation is merely a data structure that can be serialized to JSON.
 */
public class Output {
  public final class OutputOptions {
    private String input;
    private String output;
    private int duration;

    public OutputOptions(String input, String output, int duration) {
      this.input = input;
      this.output = output;
      this.duration = duration;
    }
  }

  public final class OutputVehicle {
    public final class VehicleStop {
      public String id;
      public Location location;
    }

    public String id;
    public List<VehicleStop> route;
    public double route_travel_duration;
  }

  public final class UnplannedStop {
    public String id;
    public Location location;
  }

  private final class Solution {
    private List<OutputVehicle> vehicles;
    private List<UnplannedStop> unplannedStops;
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

  private final Solution solution;
  private final Statistics statistics;

  public Output(
      List<OutputVehicle> vehicles,
      List<UnplannedStop> unplannedStops,
      double value,
      double duration,
      double runDuration) {
    this.solution = new Solution();
    this.solution.vehicles = vehicles;
    this.solution.unplannedStops = unplannedStops;
    this.solution.value = value;
    this.statistics = new Statistics();
    this.statistics.run = new StatisticsRun();
    this.statistics.run.duration = runDuration;
    this.statistics.result = new StatisticsResult();
    this.statistics.result.duration = duration;
    this.statistics.result.value = solution.value;

    // Fill custom section.
    this.statistics.result.custom = new StatisticsResultCustom();

    // A vehicle is activated if it has at least three stops. The first and last
    // stop are the depot, so the vehicle has at least one customer stop.
    this.statistics.result.custom.activatedVehicles = (int) vehicles.stream()
        .filter(v -> v.().size() > 3).count();

    // Find the vehicle with the maximum route distance.
    this.statistics.result.custom.maxRouteDistance = (int) vehicles.stream()
        .mapToDouble(v -> v.getDistance()).max().orElse(0);

    // Find the vehicle with the maximum number of stops.
    this.statistics.result.custom.maxStopsInVehicle = (int) vehicles.stream()
        .mapToDouble(v -> v.getStops().size() - 2).max().orElse(0);

    // Find the vehicle with the minimum number of stops.
    this.statistics.result.custom.minStopsInVehicle = (int) vehicles.stream()
        .mapToDouble(v -> v.getStops().size() - 2).min().orElse(0);
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
