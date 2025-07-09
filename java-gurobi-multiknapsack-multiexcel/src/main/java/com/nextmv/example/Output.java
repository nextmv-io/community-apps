package com.nextmv.example;

import java.util.List;
import java.util.ArrayList;
import java.nio.file.Files;
import java.nio.file.Paths;

import com.google.gson.Gson;

public class Output {
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

  private final Statistics statistics;

  public Output(
      double duration,
      double value,
      String provider,
      String status,
      int variables,
      int constraints) {
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
