package com.nextmv.example;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.stream.Collectors;

import com.google.gson.Gson;
import com.google.gson.annotations.SerializedName;

public class Input {
  @SerializedName(value = "distance_matrix")
  public final long[][] distanceMatrix;
  @SerializedName(value = "num_vehicles")
  public final int vehicleNumber;
  public final int depot;

  public Input(int vehicleNumber, int depot, long[][] distanceMatrix) {
    this.distanceMatrix = new long[vehicleNumber+1][vehicleNumber+1];
    this.vehicleNumber = vehicleNumber;
    this.depot = depot;
    for (int i = 0; i < vehicleNumber+1; i++) {
      for (int j = 0; j < vehicleNumber+1; j++) {
        this.distanceMatrix[i][j] = distanceMatrix[i][j];
      }
    }
  }

  public long[][] getDistanceMatrix() {
    return this.distanceMatrix;
  }

  public int getVehicleNumber() {
    return this.vehicleNumber;
  }

  public int getDepot() {
    return this.depot;
  }
  
  public static Input fromString(String path) {
    Gson gson = new Gson();
    // Read stdin if no path is provided.
    if (path.isEmpty()) {
      try (BufferedReader reader = new BufferedReader(new InputStreamReader(System.in))) {
        return gson.fromJson(
          reader.lines().collect(Collectors.joining("\n")), Input.class
        );
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
        Input.class
      );
    } catch (java.io.IOException e) {
      System.err.println("Error reading '" + path + "': " + e.getMessage());
      System.exit(1);
    }
    return null;
  }
}
