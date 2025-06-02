package com.nextmv.example;

import java.util.List;
import java.util.ArrayList;

import com.google.gson.Gson;

public class Output {
  private final class Solution {
    private List<Item> items;
    private double value;
  }

  private final class StatisticsRun {
    private double duration;
  }

  private final class StatisticsResult {
    private double value;
    private StatisticsResultCustom custom;
  }

  private final class StatisticsResultCustom {
    private String provider;
    private String status;
    private int variables;
    private int constraints;
  }

  private final class Statistics {
    private String schema = "v1";
    private StatisticsRun run;
    private StatisticsResult result;
  }

  private final List<Solution> solutions;
  private final Statistics statistics;

  public Output(
      List<Item> items,
      double duration,
      double value,
      String provider,
      String status,
      int variables,
      int constraints) {
    this.solutions = new ArrayList<Solution>();
    Solution solution = new Solution();
    solution.items = items;
    solution.value = value;
    this.solutions.add(solution);
    this.statistics = new Statistics();
    this.statistics.run = new StatisticsRun();
    this.statistics.run.duration = duration;
    this.statistics.result = new StatisticsResult();
    this.statistics.result.value = value;
    this.statistics.result.custom = new StatisticsResultCustom();
    this.statistics.result.custom.provider = provider;
    this.statistics.result.custom.status = status;
    this.statistics.result.custom.constraints = constraints;
    this.statistics.result.custom.variables = variables;
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
