package com.nextmv.example;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.List;
import java.util.stream.Collectors;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;

public class Input {
  public final class Location {
    public double lat;
    public double lon;

    public Location(double lat, double lon) {
      this.lat = lat;
      this.lon = lon;
    }
  }

  public final class Vehicle {
    public String id;

    public Vehicle(String id) {
      this.id = id;
    }
  }

  public final class Stop {
    public String id;
    public Location location;
  }

  @SerializedName(value = "duration_matrix")
  public final long[][] durationMatrix;
  public final List<Vehicle> vehicles;
  public final List<Stop> stops;

  public Input(
      long[][] durationMatrix,
      List<Vehicle> vehicles,
      List<Stop> stops) {
    if (durationMatrix != null) {
      for (long[] row : durationMatrix) {
        if (row.length != durationMatrix.length) {
          throw new IllegalArgumentException("Duration matrix must be square.");
        }
      }
      if (durationMatrix.length != stops.size() * 2 * vehicles.size()) {
        throw new IllegalArgumentException(
            "Duration matrix size does not match number of stops and vehicles (n_stops + 2 * n_vehicles).");
      }
    }

    this.durationMatrix = durationMatrix;
    this.vehicles = vehicles;
    this.stops = stops;
  }

  public static Input fromString(String path) {
    Gson gson = new Gson();
    // Read stdin if no path is provided.
    if (path.isEmpty()) {
      try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
        return gson.fromJson(
            reader.lines().collect(Collectors.joining("\n")), Input.class);
      } catch (java.io.IOException e) {
        System.err.println("Error reading stdin: " + e.getMessage());
        System.exit(1);
        return null;
      }
    }
    // Read the path otherwise.
    try {
      return gson.fromJson(
          java.nio.file.Files.readString(java.nio.file.Paths.get(path)),
          Input.class);
    } catch (java.io.IOException e) {
      System.err.println("Error reading '" + path + "': " + e.getMessage());
      System.exit(1);
    }
    return null;
  }
}
