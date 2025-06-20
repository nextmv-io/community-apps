package com.nextmv.example;

import java.util.List;
import java.util.ArrayList;

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

  public static void write(Output output) {
    // Always write to stdout.
    Gson gson = new Gson();
    System.out.println(gson.toJson(output));
    return;
  }
}
