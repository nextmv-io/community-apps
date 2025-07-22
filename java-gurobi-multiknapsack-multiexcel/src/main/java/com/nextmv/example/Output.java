package com.nextmv.example;

import java.nio.file.Files;
import java.nio.file.Paths;

import com.google.gson.Gson;

/**
 * Output class to wrapping the result of the optimization run.
 * Since this app outputs non-JSON data, the output only contains
 * the statistics of the run. The solution is written to separate
 * files in the output directory.
 */
public class Output {
  /**
   * StatisticsRun contains more generic metrics about the run.
   */
  private final class StatisticsRun {
    private double duration;
  }

  /**
   * StatisticsResult contains metrics about the optimization result.
   */
  private final class StatisticsResult {
    private double value;
    private StatisticsResultCustom custom;
  }

  /**
   * StatisticsResultCustom contains custom metrics about the optimization
   * result.
   */
  private final class StatisticsResultCustom {
    private String provider;
    private String status;
    private int variables;
    private int constraints;
    private int items;
    private int knapsacks;
    private int assigned;
    private int unassigned;
  }

  /**
   * Statistics is the root object for the metrics/statistics.
   */
  private final class Statistics {
    private String schema = "v1";
    private StatisticsRun run;
    private StatisticsResult result;
  }

  /**
   * The statistics object that contains all the metrics.
   */
  private final Statistics statistics;

  public Output(
      double duration,
      double value,
      String provider,
      String status,
      int variables,
      int constraints,
      int items,
      int knapsacks,
      int assigned,
      int unassigned) {
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
    this.statistics.result.custom.items = items;
    this.statistics.result.custom.knapsacks = knapsacks;
    this.statistics.result.custom.assigned = assigned;
    this.statistics.result.custom.unassigned = unassigned;
  }

  public static void write(Output output, String outputPath) {
    // Always write to {outputPath}/statistics/statistics.json
    // as required by convention.
    Gson gson = new Gson();
    String json = gson.toJson(output);
    java.nio.file.Path path = Paths.get(outputPath, "statistics", "statistics.json");
    try {
      Files.createDirectories(path.getParent());
      Files.writeString(path, json);
    } catch (java.io.IOException e) {
      System.err.println("Failed to write output: " + e.getMessage());
      System.exit(1);
    }
  }
}
