package com.nextmv.example;

import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;

import com.gurobi.gurobi.*;

public final class Main {

  /**
   * Main entry point for the application.
   * 
   * @param args Command line arguments.
   */
  public static void main(String[] args) {
    try {
      // Parse arguments.
      Options options = Options.fromArguments(args);

      // Make sure input directory exists.
      Path inputPath = Paths.get(options.getInputPath());
      if (!inputPath.toFile().exists() || !inputPath.toFile().isDirectory()) {
        System.err.println("Input directory does not exist: " + options.getInputPath());
        System.exit(1);
      }
      // Prepare output directory.
      prepareOutputDirectory(options.getOutputPath());

      // Load input.
      ExcelReader inputReader = new ExcelReader();
      Input input;
      try {
        String inputFilePath = Paths.get(options.getInputPath(), "input.xlsx").toString();
        input = inputReader.readExcelFile(inputFilePath);
      } catch (Exception e) {
        System.err.println("Error reading input file: " + e.getMessage());
        System.exit(1);
        return; // Unreachable, but added for completeness
      }
      if (input.getItems().isEmpty() || input.getKnapsacks().isEmpty()) {
        System.err.println("Input file must contain at least one item and one knapsack.");
        System.exit(1);
      }

      // Setup Gurobi environment and model.
      GRBEnv env = new GRBEnv(true);
      // env.set("OutputFlag", "0"); // Disable output if needed
      env.start();
      GRBModel model = new GRBModel(env);

      // Apply duration limit.
      model.set(GRB.DoubleParam.TimeLimit, options.getDuration());

      // Create assignment variable for each item in each knapsack.
      // Variables are binary, indicating whether an item is assigned to a knapsack.
      List<GRBVar> variables = new ArrayList<>();
      List<Item> items = input.getItems();
      List<Knapsack> knapsacks = input.getKnapsacks();
      for (Knapsack knapsack : knapsacks) {
        for (Item item : items) {
          variables.add(model.addVar(0.0, 1.0, 0.0, GRB.BINARY, knapsack.getId() + "_" + item.getId()));
        }
      }

      // Integrate new variables
      model.update();

      // Create capacity constraint.
      for (int i = 0; i < knapsacks.size(); ++i) {
        Knapsack knapsack = knapsacks.get(i);
        GRBLinExpr knapsackExpr = new GRBLinExpr();
        for (int j = 0; j < items.size(); ++j) {
          knapsackExpr.addTerm(items.get(j).getWeight(), variables.get(i * items.size() + j));
        }
        model.addConstr(knapsackExpr, GRB.LESS_EQUAL, knapsack.getCapacity(), "capacity_" + knapsack.getId());
      }

      // Ensure that each item can only be assigned once.
      for (int j = 0; j < items.size(); ++j) {
        GRBLinExpr itemExpr = new GRBLinExpr();
        for (int i = 0; i < knapsacks.size(); ++i) {
          itemExpr.addTerm(1.0, variables.get(i * items.size() + j));
        }
        model.addConstr(itemExpr, GRB.LESS_EQUAL, 1.0, "item_assignment_" + items.get(j).getId());
      }

      // Create the objective function.
      GRBLinExpr objectiveExpr = new GRBLinExpr();
      for (int i = 0; i < knapsacks.size(); ++i) {
        for (int j = 0; j < items.size(); ++j) {
          objectiveExpr.addTerm(items.get(j).getValue(), variables.get(i * items.size() + j));
        }
      }
      model.setObjective(objectiveExpr, GRB.MAXIMIZE);

      // Solve.
      model.optimize();

      // Convert to solution.
      List<Assignment> assignments = new ArrayList<>();
      Set<String> unassignedItems = new HashSet<>();
      for (int i = 0; i < variables.size(); ++i) {
        int knapsackIndex = i / items.size();
        int itemIndex = i % items.size();
        if (variables.get(i).get(GRB.DoubleAttr.X) > 0.5) {
          assignments
              .add(new Assignment(items.get(itemIndex).getId(), knapsacks.get(knapsackIndex).getId()));
        } else {
          unassignedItems.add(items.get(itemIndex).getId());
        }
      }
      Solution solution = new Solution(assignments, new ArrayList<>(unassignedItems));
      // Write solution to Excel file.
      ExcelWriter outputWriter = new ExcelWriter();
      try {
        String solutionPath = Paths.get(options.getOutputPath(), "solutions", "solution.xlsx").toString();
        outputWriter.writeSolutionToExcel(solution, solutionPath);
      } catch (Exception e) {
        System.err.println("Error writing output file: " + e.getMessage());
        System.exit(1);
      }

      // Convert solution to output.
      Output output = new Output(
          model.get(GRB.DoubleAttr.Runtime),
          model.get(GRB.DoubleAttr.ObjVal),
          "Gurobi",
          convertStatus(model.get(GRB.IntAttr.Status)),
          model.get(GRB.IntAttr.NumVars),
          model.get(GRB.IntAttr.NumConstrs),
          items.size(),
          knapsacks.size(),
          assignments.size(),
          unassignedItems.size());

      // Write output.
      Output.write(output, options.getOutputPath());

      // Dispose of model and environment.
      model.dispose();
      env.dispose();

    } catch (GRBException e) {
      System.out.println("Error code: " + e.getErrorCode() + ". " + e.getMessage());
      e.printStackTrace();
    }
  }

  /**
   * Prepares the output directory by creating necessary subdirectories.
   * 
   * @param outputPath The path to the output directory.
   */
  private static void prepareOutputDirectory(String outputPath) {
    // Prepare output directory if it does not exist.
    Path solutionsPath = Paths.get(outputPath, "solutions");
    Path statisticsPath = Paths.get(outputPath, "statistics");
    if (!solutionsPath.toFile().exists()) {
      if (!solutionsPath.toFile().mkdirs()) {
        System.err.println("Failed to create solutions directory: " + solutionsPath.toString());
        System.exit(1);
      }
    } else if (!solutionsPath.toFile().isDirectory()) {
      System.err.println("Solutions path is not a directory: " + solutionsPath.toString());
      System.exit(1);
    }
    if (!statisticsPath.toFile().exists()) {
      if (!statisticsPath.toFile().mkdirs()) {
        System.err.println("Failed to create statistics directory: " + statisticsPath.toString());
        System.exit(1);
      }
    } else if (!statisticsPath.toFile().isDirectory()) {
      System.err.println("Statistics path is not a directory: " + statisticsPath.toString());
      System.exit(1);
    }
  }

  /**
   * Converts Gurobi status codes to human-readable strings.
   *
   * @param status The Gurobi status code.
   * @return A string representation of the status.
   */
  public static String convertStatus(int status) {
    switch (status) {
      case GRB.Status.LOADED:
        return "LOADED";
      case GRB.Status.OPTIMAL:
        return "OPTIMAL";
      case GRB.Status.INFEASIBLE:
        return "INFEASIBLE";
      case GRB.Status.INF_OR_UNBD:
        return "INF_OR_UNBD";
      case GRB.Status.UNBOUNDED:
        return "UNBOUNDED";
      case GRB.Status.CUTOFF:
        return "CUTOFF";
      case GRB.Status.ITERATION_LIMIT:
        return "ITERATION_LIMIT";
      case GRB.Status.NODE_LIMIT:
        return "NODE_LIMIT";
      case GRB.Status.TIME_LIMIT:
        return "TIME_LIMIT";
      case GRB.Status.SOLUTION_LIMIT:
        return "SOLUTION_LIMIT";
      case GRB.Status.INTERRUPTED:
        return "INTERRUPTED";
      case GRB.Status.NUMERIC:
        return "NUMERIC";
      case GRB.Status.SUBOPTIMAL:
        return "SUBOPTIMAL";
      case GRB.Status.INPROGRESS:
        return "INPROGRESS";
      case GRB.Status.USER_OBJ_LIMIT:
        return "USER_OBJ_LIMIT";
      case GRB.Status.WORK_LIMIT:
        return "WORK_LIMIT";
      case GRB.Status.MEM_LIMIT:
        return "MEM_LIMIT";
      default:
        return "UNKNOWN";
    }
  }
}
