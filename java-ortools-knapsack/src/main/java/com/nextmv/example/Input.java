package com.nextmv.example;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.util.List;
import java.util.stream.Collectors;

import com.google.gson.Gson;

public class Input {
  private final List<Item> items;
  private final double weightCapacity;

  public Input(List<Item> items, double weightCapacity) {
    this.items = items;
    this.weightCapacity = weightCapacity;
  }

  public List<Item> getItems() {
    return this.items;
  }

  public double getWeightCapacity() {
    return this.weightCapacity;
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
