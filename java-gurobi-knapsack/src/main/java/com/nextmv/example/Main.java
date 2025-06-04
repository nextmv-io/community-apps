package com.nextmv.example;

import java.util.ArrayList;
import java.util.List;

import com.gurobi.gurobi.*;

public final class Main {

  public static void main(String[] args) {
    try {
      // Parse arguments.
      Options options = Options.fromArguments(args);

      // Load input.
      Input input = Input.fromString(options.getInputPath());

      // Setup Gurobi environment and model.
      GRBEnv env = new GRBEnv(true);
      env.set("OutputFlag", "0"); // Disable output
      env.start();
      GRBModel model = new GRBModel(env);

      // Apply duration limit.
      model.set(GRB.DoubleParam.TimeLimit, options.getDuration());

      // Create assignment variable for each item.
      List<GRBVar> variables = new ArrayList<>();
      List<Item> inputItems = input.getItems();
      for (Item item : inputItems) {
        variables.add(model.addVar(0.0, 1.0, 0.0, GRB.BINARY, item.getId()));
      }

      // Integrate new variables
      model.update();

      // Create capacity constraint.
      GRBLinExpr capacityExpr = new GRBLinExpr();
      for (int i = 0; i < variables.size(); ++i) {
        capacityExpr.addTerm(inputItems.get(i).getWeight(), variables.get(i));
      }
      model.addConstr(capacityExpr, GRB.LESS_EQUAL, input.getWeightCapacity(), "capacity");

      // Create the objective function.
      GRBLinExpr objectiveExpr = new GRBLinExpr();
      for (int i = 0; i < variables.size(); ++i) {
        objectiveExpr.addTerm(inputItems.get(i).getValue(), variables.get(i));
      }
      model.setObjective(objectiveExpr, GRB.MAXIMIZE);

      // Solve.
      model.optimize();

      // Convert solution to output.
      List<Item> outputItems = new ArrayList<>();
      for (int i = 0; i < variables.size(); ++i) {
        if (variables.get(i).get(GRB.DoubleAttr.X) > 0.5) {
          outputItems.add(inputItems.get(i));
        }
      }
      Output output = new Output(
          outputItems,
          model.get(GRB.DoubleAttr.Runtime),
          model.get(GRB.DoubleAttr.ObjVal),
          "Gurobi",
          convertStatus(model.get(GRB.IntAttr.Status)),
          model.get(GRB.IntAttr.NumVars),
          model.get(GRB.IntAttr.NumConstrs));

      // Write output.
      Output.write(options.getOutputPath(), output);

      // Dispose of model and environment.
      model.dispose();
      env.dispose();

    } catch (GRBException e) {
      System.out.println("Error code: " + e.getErrorCode() + ". " + e.getMessage());
      e.printStackTrace();
    }
  }

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
