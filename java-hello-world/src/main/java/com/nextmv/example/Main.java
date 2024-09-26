package com.nextmv.example;

import com.google.gson.Gson;
import java.io.FileReader;
import java.io.IOException;
import com.google.gson.JsonObject;

public class Main {
  public static void main(String[] args) {
      Gson gson = new Gson();
      
      
      try (FileReader reader = new FileReader("input.json")) {
          // Read from stdin.
          Input input = gson.fromJson(reader, Input.class);

          // ##### Insert model here
          
          // Print logs that render in the run view in Nextmv Console
          System.err.println("Hello, " + input.name);
          
          // Write output and statistics.
          Output output = new Output(input.name);
          Output.write(output);
      } catch (IOException e) {
          e.printStackTrace();
      }
  }
}


class Input {
    String name;
}


class Output {
    JsonObject options = new JsonObject();
    Solution solution;
    Statistics statistics;

    public Output(String name) {
        this.solution = new Solution();
        this.statistics = new Statistics();
        this.statistics.result = new StatisticsResult();
        this.statistics.result.value = 1.23;
        this.statistics.result.custom = new StatisticsResultCustom();
        this.statistics.result.custom.message = "Hello, " + name;
    }

    public static void write(Output output) {
        Gson gson = new Gson();
        System.out.println(gson.toJson(output));
    }
}

class Solution {}

class StatisticsResult {
    public double value;
    public StatisticsResultCustom custom;
}

class StatisticsResultCustom {
    public String message;
}

class Statistics {
    public String schema = "v1";
    public StatisticsResult result;
}


